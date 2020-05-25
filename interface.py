# *****************************************************************************
# * Author: Miguel Magalhaes
# * Email: miguel@magalhaes.pro
# *****************************************************************************
# * Interface
# *****************************************************************************

import cv2 as cv
import json
import webbrowser
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtSvg import *
from PyQt5.QtWebEngineWidgets import *

from config import VIDEO
from camera import Camera
from tracking import Tracking
from fps import FPS
from rendering import Rendering

class Interface(QWidget):
    def __init__(self, path, config):
        QWidget.__init__(self)

        self.path = path
        self.config = config

        self.setWindowTitle('AR4maps')
        self.move(0,0)
        self.video_size = QSize(VIDEO.WIDTH, VIDEO.HEIGHT)
        self.setup_ui()
        
        self.markerImg = cv.imread(self.path + self.config['target'])
        # cv.imshow("target",targetImg)
        self._cam = Camera().start()
        self._track = Tracking(self.markerImg)
        self._rendering = Rendering(self.markerImg, self.config['coords'])
        self._fps = FPS()
        
        self.setup_render()

    def setup_ui(self):
        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        
        ### CENTER LAYOUT
        self.center_layout = QVBoxLayout()
        self.main_layout.addLayout(self.center_layout)

        # AR
        self.pixmap = QLabel()
        self.pixmap.setFixedSize(self.video_size)
        self.pixmap.mousePressEvent = self.click_pixmap
        self.center_layout.addWidget(self.pixmap)

        ## SOUTH LAYOUT
        self.south_layout = QVBoxLayout()
        self.south_layout.setContentsMargins(20,10,20,20)
        self.center_layout.addLayout(self.south_layout)
        # Feature Description
        #   Title
        self.feature_title = QLabel('<br/>')
        self.feature_title.setFont(QFont('Helvetica', 18))
        self.south_layout.addWidget(self.feature_title)
        #   Description
        self.feature_description = QLabel('<br/><br/><br/><br/><br/>')
        self.feature_description.setWordWrap(True)
        self.south_layout.addWidget(self.feature_description)
        self.south_layout.addStretch()
        #   Buttons
        self.south_btns_layout = QHBoxLayout()
        self.south_layout.addLayout(self.south_btns_layout)
        self.feature_website_btn = QPushButton('Website')
        self.feature_website_btn.hide()
        self.south_btns_layout.addWidget(self.feature_website_btn)
        self.feature_photos_btn = QPushButton('Photos')
        self.feature_photos_btn.hide()
        self.south_btns_layout.addWidget(self.feature_photos_btn)
        self.feature_video_btn = QPushButton('Video')
        self.feature_video_btn.hide()
        self.south_btns_layout.addWidget(self.feature_video_btn)
        self.south_btns_layout.addStretch()

        ### EAST LAYOUT
        self.east_layout = QVBoxLayout()
        self.east_layout.setContentsMargins(0,10,20,20)
        self.main_layout.addLayout(self.east_layout)
        # Logo
        self.logo = QSvgWidget(self.path + self.config['logo'])
        self.logo.setMinimumSize(252,129)
        self.logo.setMaximumSize(252,129)
        self.east_layout.addWidget(self.logo)
        # Buttons
        for layer in self.config['layers']:
            btn = QPushButton(layer['name'])
            btn.clicked.connect(lambda state, x=layer: self.load_layer(x))
            self.east_layout.addWidget(btn)
        # Layer Description
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        self.east_layout.addWidget(sep)
        self.layer_title = QLabel('Select a layer...')
        self.layer_title.setFont(QFont('Helvetica', 18))
        self.east_layout.addWidget(self.layer_title)
        self.layer_description = QLabel('')
        self.layer_description.setWordWrap(True)
        self.east_layout.addWidget(self.layer_description)
        # FPS
        self.east_layout.addStretch()
        self.fps_label = QLabel()
        self.fps_label.setAlignment(Qt.AlignRight)
        self.east_layout.addWidget(self.fps_label)

        self.setLayout(self.main_layout)

        self.web = QWebEngineView()
        self.web.resize(VIDEO.WIDTH, VIDEO.HEIGHT)
        self.web.move(0,0)
        self.web.hide()

    def load_layer(self, layer):
        self.layer_title.setText(layer['name'])
        self.layer_description.setText(layer['description'])
        self.feature_title.setText('Select an item on the screen...')
        self.feature_description.setText('')
        self._rendering.setHighlighted(None)
        self.feature_website_btn.hide()
        self.feature_photos_btn.hide()
        self.feature_video_btn.hide()
        with open(self.path + layer['file']) as json_file:
            data = json.load(json_file)
            self._rendering.setGeoJSON(data['features'])

    def click_pixmap(self, event):
        pos = (event.x(), event.y())
        feature = self._rendering.getClickedFeature(pos)
        self.feature_website_btn.hide()
        self.feature_photos_btn.hide()
        self.feature_video_btn.hide()
        if feature is not None:
            props = feature['properties']
            self.feature_title.setText(props['title'] if 'title' in props else 'NO TITLE')
            self.feature_description.setText(props['description'] if 'description' in props else '')
            self._rendering.setHighlighted(feature['uuid'])
            if 'website' in props:
                self.feature_website_btn.show()
                try: self.feature_website_btn.clicked.disconnect()
                except Exception: pass
                self.feature_website_btn.clicked.connect(lambda state, x=props['website']: webbrowser.open(x))
            if 'photos' in props:
                self.feature_photos_btn.show()
                try: self.feature_photos_btn.clicked.disconnect()
                except Exception: pass
                self.feature_photos_btn.clicked.connect(lambda state, x=props['photos']: self.display_photos(x))
            if 'video' in props:
                self.feature_video_btn.show()
                try: self.feature_video_btn.clicked.disconnect()
                except Exception: pass
                self.feature_video_btn.clicked.connect(lambda state, x=props['video']: self.display_video(x))
        else:
            self.feature_title.setText('')
            self.feature_description.setText('')
            self._rendering.setHighlighted(None)

    def display_photos(self, photos):
        photos = list(map(lambda x: self.path + x, photos))
        self.slideshow = SlideShow(photos)
        self.slideshow.show()

    def display_video(self, url):
        self.web.load(QUrl(url))
        self.web.show()

    def setup_render(self):
        self._fps.start()
        self.timer = QTimer()
        self.timer.timeout.connect(self.render)
        self.timer.start(1000 / VIDEO.FPS)

    def render(self):
        _, frameImg = self._cam.read()
        frameImg = cv.cvtColor(frameImg, cv.COLOR_BGR2RGB)
        H = self._track.update(frameImg)
        self._rendering.update(H, frameImg)
        if(H is not None):
            # self._rendering.drawBorder()
            self._rendering.renderGeoJSON()
            # self._rendering.renderObj()

        image = QImage(frameImg, frameImg.shape[1], frameImg.shape[0], 
                       frameImg.strides[0], QImage.Format_RGB888)
        self.pixmap.setPixmap(QPixmap.fromImage(image))
        self.fps_label.setText("{:.2f} FPS".format(self._fps.update()))
  
    def closeEvent(self, event):
        self._cam.stop()
        self._fps.stop()
        print("\033[0;30;102m[INFO]\033[0m {:.2f} seconds".format(self._fps.elapsed()))
        print("\033[0;30;102m[INFO]\033[0m {:.2f} FPS".format(self._fps.fps()))


class SlideShow(QWidget):
    def __init__(self, photos):
        super().__init__()
        self.setWindowTitle("Photos")
        self.photos = photos
        self.i = 0
        self.initUI()

    def keyPressEvent(self, event):
        key=event.key()
        if key == Qt.Key_Right:
            self.i += 1
        elif key == Qt.Key_Left:
            self.i -= 1
        self.show_image()

    def initUI(self):
        self.setGeometry(0, 0, 1280, 720)

        self.main_layout = QHBoxLayout()
        self.main_layout.setContentsMargins(0,0,0,0)
        self.setLayout(self.main_layout)
        
        # Previous Btn
        self.prev_btn = QPushButton('⬅')
        self.prev_btn.clicked.connect(self.prev_image)
        self.main_layout.addWidget(self.prev_btn)

        # Pixmap
        self.main_layout.addStretch()
        self.pixmap = QLabel(self)
        self.main_layout.addWidget(self.pixmap)
        self.main_layout.addStretch()
        
        # Next Btn
        self.prev_btn = QPushButton('⮕')
        self.prev_btn.clicked.connect(self.prev_image)
        self.main_layout.addWidget(self.prev_btn)

        self.show_image()
        self.show()

    def prev_image(self):
        self.i -= 1
        self.show_image()

    def next_image(self):
        self.i += 1
        self.show_image()

    def show_image(self):
        pixmap = QPixmap(self.photos[self.i % len(self.photos)])
        pixmap = pixmap.scaled(1280, 720, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.pixmap.setPixmap(pixmap)
