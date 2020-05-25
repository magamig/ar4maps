# *****************************************************************************
# * Author: Miguel Magalhaes
# * Email: miguel@magalhaes.pro
# *****************************************************************************
# * Rendering
# *****************************************************************************

import cv2 as cv
import numpy as np
import math
import uuid 
from PIL import ImageColor

from config import RENDER

class Rendering:
    def __init__(self, markerImg, coords2pixels):
        self.coords2pixels = coords2pixels
        self.K = np.array([[1642, 0, 1176], [0, 1642, 714], [0, 0, 1]])
        self.H = None
        self.geojson = None
        self.h, self.w, _ = markerImg.shape
        self.frameImg = None
        self.highlighted = None

    def update(self, H, frameImg):
        self.H = H
        self.frameImg = frameImg

    def drawBorder(self):
        pts = [[0,0],[self.w,0],[self.w,self.h],[0,self.h]]
        pts = cv.perspectiveTransform(np.float32([pts]), self.H)[0]
        pts = list(map(tuple, pts))
        cv.line(self.frameImg, pts[0], pts[1], (0,255,0), 3, cv.LINE_AA)
        cv.line(self.frameImg, pts[1], pts[2], (0,255,0), 3, cv.LINE_AA)
        cv.line(self.frameImg, pts[2], pts[3], (0,255,0), 3, cv.LINE_AA)
        cv.line(self.frameImg, pts[3], pts[0], (0,255,0), 3, cv.LINE_AA)

    def setGeoJSON(self, features):
        self.geojson = GeoJSON(features, self.coords2pixels)

    def renderGeoJSON(self):
        if self.geojson is not None:
            overlayImg = self.frameImg.copy()
            for f in self.geojson.features:
                props = f['properties']
                geo = f['geometry']
                color = ImageColor.getcolor(props['fill'], 'RGB') if 'fill' in props else None
                # print(geo,props)
                if geo['type'] == 'Point':
                    color = color or RENDER.POINT_COLOR
                    pts = np.float32([[geo['coordinates']]])
                    pts = cv.perspectiveTransform(pts, self.H)[0][0]
                    pts = tuple(pts)
                    cv.circle(overlayImg, pts, RENDER.POINT_RADIUS, color, -1, cv.LINE_AA)
                    if self.highlighted == f['uuid']:
                        cv.circle(self.frameImg, pts, RENDER.POINT_RADIUS, color, -1, cv.LINE_AA)
                        cv.circle(self.frameImg, pts, RENDER.POINT_RADIUS + 13, color, 3, cv.LINE_AA)
                elif geo['type'] == 'MultiPoint':
                    color = color or RENDER.LINE_COLOR
                    for pts in geo['coordinates']:
                        pts = np.float32([[pts]])
                        pts = cv.perspectiveTransform(pts, self.H)[0][0]
                        pts = tuple(pts)
                        cv.circle(overlayImg, pts, RENDER.POINT_RADIUS, color, -1, cv.LINE_AA)
                        if self.highlighted == f['uuid']:
                            cv.circle(self.frameImg, pts, RENDER.POINT_RADIUS, color, -1, cv.LINE_AA)
                            cv.circle(self.frameImg, pts, RENDER.POINT_RADIUS + 13, color, 3, cv.LINE_AA)     
                elif geo['type'] == 'LineString':
                    color = color or RENDER.LINE_COLOR
                    pts = np.float32([geo['coordinates']])
                    pts = cv.perspectiveTransform(pts, self.H)[0]
                    cv.polylines(overlayImg, np.int32([pts]), False, color, RENDER.LINE_THICKNESS, cv.LINE_AA)
                    if self.highlighted == f['uuid']:
                        cv.polylines(self.frameImg, np.int32([pts]), False, color, RENDER.LINE_THICKNESS, cv.LINE_AA)
                elif geo['type'] == 'MultiLineString':
                    color = color or RENDER.LINE_COLOR
                    for pts in geo['coordinates']:
                        pts = np.float32([pts])
                        pts = cv.perspectiveTransform(pts, self.H)[0]
                        cv.polylines(overlayImg, np.int32([pts]), False, color, RENDER.LINE_THICKNESS, cv.LINE_AA)
                        if self.highlighted == f['uuid']:
                            cv.polylines(self.frameImg, np.int32([pts]), False, color, RENDER.LINE_THICKNESS, cv.LINE_AA)        
                elif geo['type'] == 'Polygon':
                    pts = np.float32([geo['coordinates'][0]])
                    pts = cv.perspectiveTransform(pts, self.H)[0]
                    if color is None:
                        cv.polylines(overlayImg, np.int32([pts]), False, RENDER.POLYGON_BORDER_COLOR, RENDER.LINE_THICKNESS, cv.LINE_AA)    
                        color = RENDER.POLYGON_COLOR
                    cv.fillPoly(overlayImg, np.int32([pts]), color, cv.LINE_AA)
                    if self.highlighted == f['uuid']:
                        cv.fillPoly(self.frameImg, np.int32([pts]), color, cv.LINE_AA)
                elif geo['type'] == 'MultiPolygon':
                    color = color or RENDER.POLYGON_COLOR
                    for pts in geo['coordinates']:
                        pts = np.float32(pts)
                        pts = cv.perspectiveTransform(pts, self.H)[0]
                        if color == RENDER.POLYGON_COLOR:
                            cv.polylines(overlayImg, np.int32([pts]), False, RENDER.POLYGON_BORDER_COLOR, RENDER.LINE_THICKNESS, cv.LINE_AA)    
                        cv.fillPoly(overlayImg, np.int32([pts]), color, cv.LINE_AA)
                        if self.highlighted == f['uuid']:
                            cv.fillPoly(self.frameImg, np.int32([pts]), color, cv.LINE_AA)
            cv.addWeighted(overlayImg, RENDER.OPACITY, self.frameImg, 1 - RENDER.OPACITY, 0, self.frameImg)

    def getClickedFeature(self, pos):
        feature = None
        if self.H is not None and self.geojson is not None:
            pos = np.float32([[list(pos)]])
            pos = cv.perspectiveTransform(pos, np.linalg.inv(self.H))[0][0]
            pos = tuple(pos)
            for f in self.geojson.features:
                geo = f['geometry']
                if geo['type'] == 'Point':
                    ax, ay = tuple(geo['coordinates'])
                    bx, by = pos
                    xDiff = ax - bx
                    yDiff = ay - by
                    if math.sqrt((xDiff * xDiff) + (yDiff * yDiff)) < RENDER.POINT_RADIUS:
                        feature = f
                elif geo['type'] == 'Polygon':
                    if cv.pointPolygonTest(np.int32(geo['coordinates'][0]), pos, False) == 1:
                        feature = f
                elif geo['type'] == 'MultiPolygon':
                    for pts in geo['coordinates']:
                        if cv.pointPolygonTest(np.int32(pts[0]), pos, False) == 1:
                            feature = f
        return feature

    def setHighlighted(self, feature_uuid):
        self.highlighted = feature_uuid

class GeoJSON:
    def __init__(self, features, coords2pixels):
        self.features = features
        order = ['Point','MultiPoint','LineString','MultiLineString','Polygon','MultiPolygon']
        self.features.sort(key=lambda x: order.index(x['geometry']['type']), reverse=True)

        src = np.array(coords2pixels['src'], np.float32)
        dst = np.array(coords2pixels['dst'], np.float32)
        M = cv.getAffineTransform(src,dst)
        M = np.append(M, [[0,0,1]], axis=0)
        
        for f in self.features:
            geoType = f['geometry']['type']
            f['uuid'] = str(uuid.uuid1())
            if geoType == 'Point':
                f['geometry']['coordinates'] = self.coords2pixels([f['geometry']['coordinates']], M)[0]
            elif geoType == 'LineString':
                f['geometry']['coordinates'] = self.coords2pixels(f['geometry']['coordinates'], M)
            elif geoType == 'Polygon':
                for i, coords in enumerate(f['geometry']['coordinates']):
                    f['geometry']['coordinates'][i] = self.coords2pixels(coords, M)
            elif geoType == 'MultiPolygon':
                for i, coordsList in enumerate(f['geometry']['coordinates']):
                    for j, coords in enumerate(coordsList):
                        f['geometry']['coordinates'][i][j] = self.coords2pixels(coords, M)

    def coords2pixels(self, coords, M):
        # switch lat long and perspectiveTransform
        coords = np.transpose(coords)
        coords = [coords[1], coords[0]]
        coords = np.transpose(coords)
        coords = cv.perspectiveTransform(np.float32([coords]), M)[0]
        return coords.tolist()
