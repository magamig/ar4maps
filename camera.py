# *****************************************************************************
# * Author: Miguel Magalhaes
# * Email: miguel@magalhaes.pro
# *****************************************************************************
# * Camera
# *****************************************************************************

import cv2 as cv
from threading import Thread

from config import VIDEO

class Camera:
    def __init__(self):
        self._stream = cv.VideoCapture(VIDEO.SRC)
        self._stream.set(cv.CAP_PROP_FRAME_WIDTH, VIDEO.WIDTH)
        self._stream.set(cv.CAP_PROP_FRAME_HEIGHT, VIDEO.HEIGHT)
        self._stream.set(cv.CAP_PROP_FPS, VIDEO.FPS)
        (self._flag, self._frame) = self._stream.read()
        self._stopped = False
    
    def start(self):
        Thread(target=self.update, args=()).start()
        return self
    
    def update(self):
        while not self._stopped:
            self._flag, self._frame = self._stream.read()

    def read(self):
        return self._flag, self._frame

    def stop(self):
        self._stopped = True
