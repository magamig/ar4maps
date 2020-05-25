# *****************************************************************************
# * Author: Miguel Magalhaes
# * Email: miguel@magalhaes.pro
# *****************************************************************************
# * Tracking
# *****************************************************************************

import cv2 as cv
import numpy as np
import copy

class Tracking:
    LOWES_RATIO = 0.7

    min_matches = 50
    index_params = dict(
        algorithm = 6, # FLANN_INDEX_LSH
        table_number = 6,
        key_size = 10,
        multi_probe_level = 1)
    search_params = dict(checks=50)
    flann = cv.FlannBasedMatcher(
        index_params,
        search_params)
    lk_params = dict(
        winSize  = (8,8),
        maxLevel = 8,
        criteria = (cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.01))

    def __init__(self, markerImg):
        self.marker = FeatureExtraction(markerImg)
        self.marker.detect_and_compute()
        self.prev_frame = None
        self.frame = None
        self._numFrames = 0
        self.H = None
    
    def update(self, frameImg):
        self._numFrames += 1
        self.marker.matched_pts = []
        self.prev_frame = copy.copy(self.frame)
        self.frame = FeatureExtraction(frameImg)

        if(self.H is not None):
            self.optical_flow()
            if(len(self.frame.matched_pts) > self.min_matches * 25):
                self.H = self.pose_estimation(self.prev_frame, self.frame).dot(self.H)
            else:
                self.H = None
        
        if(self.H is None and self._numFrames % 10 == 0):
            self.H = None
            self.frame.detect_and_compute()
            self.feature_matching()
            if(len(self.marker.matched_pts) > self.min_matches):
                self.H = self.pose_estimation(self.marker, self.frame)
        
        return self.H

    def feature_matching(self):
        matches = [] # good matches as per Lowe's ratio test
        if(self.frame.des is not None and len(self.frame.des) > 2):
            all_matches = self.flann.knnMatch(self.marker.des, self.frame.des, k=2)
            try:
                for m,n in all_matches:
                    if m.distance < self.LOWES_RATIO * n.distance:
                        matches.append(m)
            except ValueError:
                pass
            if(len(matches) > self.min_matches):    
                self.marker.matched_pts = np.float32([ self.marker.kps[m.queryIdx].pt for m in matches ]).reshape(-1,1,2)
                self.frame.matched_pts = np.float32([ self.frame.kps[m.trainIdx].pt for m in matches ]).reshape(-1,1,2)

    def optical_flow(self):
        if(not len(self.prev_frame.pts)):
            self.prev_frame.convert_kps()
        self.frame.pts, st, err = cv.calcOpticalFlowPyrLK(self.prev_frame.gray_img, self.frame.gray_img, self.prev_frame.pts, None, **self.lk_params)
        st = list(np.concatenate(st)) # flatten list
        self.prev_frame.matched_pts = np.float32([ self.prev_frame.pts[i] for i in range(len(st)) if st[i] == 1 ]).reshape(-1,1,2)
        self.frame.matched_pts = np.float32([ self.frame.pts[i] for i in range(len(st)) if st[i] == 1 ]).reshape(-1,1,2)

    def pose_estimation(self, src, dst):
        H, _ = cv.findHomography(src.matched_pts, dst.matched_pts, cv.RANSAC, 5.0)
        return H

class FeatureExtraction:
    orb = cv.ORB_create(
        nfeatures=5000,
        scaleFactor=1.1,
        scoreType=cv.ORB_FAST_SCORE)

    def __init__(self, img):
        self.img = copy.copy(img)
        self.gray_img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        self.kps, self.des = [], None
        self.pts = []
        self.matched_pts = []

    def detect_and_compute(self):
        self.kps = self.orb.detect(self.gray_img, None)
        self.kps, self.des = self.orb.compute(self.gray_img, self.kps)

    def convert_kps(self):
        self.pts = cv.KeyPoint_convert(self.kps)
