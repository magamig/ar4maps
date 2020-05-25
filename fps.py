# *****************************************************************************
# * Author: Miguel Magalhaes
# * Email: miguel@magalhaes.pro
# *****************************************************************************
# * FPS
# *****************************************************************************

import datetime

class FPS:
    def __init__(self):
        self._start = None
        self._last = None
        self._end = None
        self._numFrames = 0
    
    def start(self):
        self._start = datetime.datetime.now()
        self._last = self._start
        return self
    
    def stop(self):
        self._end = datetime.datetime.now()
    
    def update(self):
        current_fps = 1 / (datetime.datetime.now() - self._last).total_seconds()
        self._last = datetime.datetime.now()
        self._numFrames += 1
        return current_fps
    
    def elapsed(self):
        # return the total number of seconds between the start and end interval
        return (self._end - self._start).total_seconds()
    
    def fps(self):
        # compute the (approximate) frames per second
        return self._numFrames / self.elapsed()
 