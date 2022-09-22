import numpy as np
import logging

# Set up logger for this module
logger = logging.getLogger('spike_graph')
logger.setLevel(logging.INFO)
import sys
handler = logging.StreamHandler(sys.stdout)
handler.formatter = logging.Formatter('%(asctime)s  %(name)s %(levelname)s: %(message)s')
logger.addHandler(handler)

class SpikeGraph:
    def __init__(self, screen, Rect):
        '''screen: the pgzero screen object.
        The frame will be the numpy array of current data containing the latest spike'''
        self.screen = screen
        self.Rect = Rect
        self.frame = None
        self.top_left = (1464, 44)
        self.bottom_right = (1785, 251)
        self.width = self.bottom_right[0] - self.top_left[0]
        self.height = self.bottom_right[1] - self.top_left[1]
        
        # These are in the range from 0 to height, with 0 representing the top
        self.tops = np.zeros(self.width) + 10
        self.bottoms = np.ones(self.width) + 15
    
    def set_frame(self, frame):
        global logger
        w = self.width
        self.frame = frame
        box_width = 1667 // w
        num_boxes = w
        
        maxes = np.zeros(num_boxes)
        mins = np.zeros(num_boxes)
        
        #for i in range(0, box_width):
        for i in range(0, num_boxes):
            box_start = box_width * i
            box_end = box_width * (i + 1)
            values = frame[box_start : box_end]
            
            maxes[i] = values.max()
            mins[i] = values.min()
            
        max_ = maxes.max()
        min_ = mins.min()
        range_ = max_ - min_
        
        h = self.height
        self.tops = np.array([h - int((v - min_) / range_ * h) for v in maxes])
        self.bottoms = np.array([h - int((v - min_) / range_ * h) for v in mins])
        
        #logger.info('tops: %s', self.tops)
        #logger.info('bottoms: %s', self.bottoms)
    
    def draw(self):
        RED = (200, 0, 0)
        BLACK = (0, 0, 0)
        GREEN = (0, 200, 0)
        WHITE = (255, 255, 255)
        BLUE = (0, 0, 255)
        BOX = self.Rect(self.top_left, (self.width, self.height))
        self.screen.draw.filled_rect(BOX, WHITE)
        
        l = self.screen.draw.line
        # Draw the lines
        for i in range(0, self.width):
            (left, top) = self.top_left
            x = left + i
            y1 = self.tops[i] + top
            y2 = self.bottoms[i] + top
            
            l((x, y1), (x, y2), BLACK)
            
