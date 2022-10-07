import numpy as np
import logging
import pygame

import util
import constants

# Set up logger for this module
logger = logging.getLogger('graphs')
logger.setLevel(logging.DEBUG)
import sys
handler = logging.StreamHandler(sys.stdout)
handler.formatter = logging.Formatter('%(asctime)s  %(name)s %(levelname)s: %(message)s')
logger.addHandler(handler)

class VerticalLineRing:
    '''Draws a vertical-line based signal ring using sample data. It uses
    constants.NUM_BOXES to choose the number of vertical lines on the ring.'''
    def __init__(self, screen):
        self.screen = screen
        self.samples = []
        self.present_box = 0
        self.line_extent = 25
        
        self.samples_to_show = constants.NUM_BOXES * 1667

        # These are in the range from -line_extent to +line_extent.
        # They only go up to the point where data has been provided.
        self.tops = []
        self.bottoms = []

        self.fake_tops = np.random.randint(0, self.line_extent, constants.NUM_BOXES)
        self.fake_bottoms = np.random.randint(-self.line_extent, 0, constants.NUM_BOXES)
    
    def give_samples(self, samples):
        samples = samples.astype('int32')
        self.samples = samples
        if not len(samples):
            return
    
        # Calculate tops and bottoms.
#        self.tops = np.zeros(int(self.present_angle / 360 * constants.NUM_BOXES)) + self.line_extent
#        self.bottoms = np.zeros(int(self.present_angle / 360 * constants.NUM_BOXES)) - self.line_extent

        #self.tops = self.fake_tops[:self.present_box]
        #self.bottoms = self.fake_bottoms[:self.present_box]

        # This represents the number of lines used by the present data
        num_used_lines = int(len(samples) / self.samples_to_show * constants.NUM_BOXES)
        min_ = int(np.min(samples))
        max_ = int(np.max(samples))
        range_ = max_ - min_ + 1
        # Convert it to be between -1 and +1
        maxes = np.zeros(num_used_lines)
        mins = np.zeros(num_used_lines)
        # Used for diagnostics
        averages = np.zeros(num_used_lines)
        
        box_width = self.samples_to_show // constants.NUM_BOXES
        
        #for i in range(0, box_width):
        for i in range(0, num_used_lines):
            box_start = box_width * i
            box_end = box_width * (i + 1)
            values = samples[box_start : box_end]
            
            maxes[i] = values.max()
            mins[i] = values.min()
            averages[i] = values.mean()
            
        if util.all_zeros(samples):
            logger.info('Somehow samples is all 0s in give_samples')
        
        h = 2*self.line_extent
        self.tops = np.array([- int((v - min_) / range_ * h) for v in maxes])
        self.bottoms = np.array([- int((v - min_) / range_ * h) for v in mins])

        logger.debug('means: %s', averages)
        logger.debug('maxes: %s', maxes)
        logger.debug('mins: %s', mins)

        logger.debug('self.tops: %s', self.tops)
        logger.debug('self.bottoms: %s', self.bottoms)        

    def advance_n_frames(self, n):
        self.present_box = int(self.present_box + n) % constants.NUM_BOXES

    def draw(self):
        # Draw the vertical lines
        #WHITE = (255, 255, 255)
        #BLUE = (0, 0, 255)
        num_lines = len(self.tops)
        data_start_box = (self.present_box - num_lines) % constants.NUM_BOXES
        for i in range(0, num_lines):
            color = (0, 0, int(255 * i / constants.NUM_BOXES))
        
            top = self.tops[i]
            bottom = self.bottoms[i]
            
            #print(num_lines)
            #if top == self.bottoms[i]:
            #    if num_lines == constants.NUM_BOXES:
            #        import pdb; pdb.set_trace()
            
            angle = ((data_start_box + i) * 360 / constants.NUM_BOXES) % 360
            self.draw_line(angle, top, bottom, color)
        
        # Draw the red line at present_angle
        RED = (200, 0, 0)
        self.draw_line(self.present_box * 360 / constants.NUM_BOXES, -2*self.line_extent, 0, RED)
        
    def draw_line(self, theta, top, bottom, color):
        # Calculate the coordinates for the inner end of the line
        r = constants.RING_RADIUS + top
        (inner_x, inner_y) = util.pol2cart(r, theta)
        inner_coords = util.adjust_coords(inner_x, inner_y)
        
        # Calculate the coordinates for the outer end of the line
        r = constants.RING_RADIUS + bottom
        (outer_x, outer_y) = util.pol2cart(r, theta)
        outer_coords = util.adjust_coords(outer_x, outer_y)
        
        # Finally draw the line
        pygame.draw.line(self.screen.surface, color, inner_coords, outer_coords, width = 35)

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

def draw_graph(i, d, graph_type, screen, STANDALONE):
    # Draw a rectangle behind the graph
    RED = (200, 0, 0)
    BLACK = (0, 0, 0)
    GREEN = (0, 200, 0)
    WHITE = (255, 255, 255)
    BLUE = (0, 0, 255)
    if graph_type not in ['boxes_ring','line_ring']:
        BOX = Rect((9, 99), (302, 82))
        screen.draw.filled_rect(BOX, GREEN)
    
    NEON_PINK = (251,72,196) # Positive
    GRAPE = (128,49,167) # Negative
    
    # Sample data for the graph
    if STANDALONE:
        x_data = list(range(0, constants.NUM_BOXES))
        x_data = [(x + i) % constants.NUM_BOXES for x in x_data]
        inputs = [2*np.pi*x/constants.NUM_BOXES for x in x_data]
        y_data = np.sin(inputs)  # update the data.
        abs_y_data = y_data
        #print('i', i)
        #print('x_data:', x_data)
        #print('inputs:', inputs)
        #print('y_data:', y_data)
    
        # Calculate the color and location of each rectangle and draw it
        min_value = -1.0
        max_value = +1.0
    else: # live or prerecorded mode        
        y_data = d.get_scaled_boxes()
        abs_y_data = d.get_absolute_scaled_boxes()
        min_value = -1.0
        max_value = +1.0
    
    MIDPOINT = constants.NUM_BOXES // 2
    
    # Plot the data
    for x, (y, abs_y) in enumerate(zip(y_data, abs_y_data)):
        if x == MIDPOINT:
            # A single white line
            color = WHITE
            abs_y = 0
        elif x == 0:
            # A black line at the origin
            color = RED
            abs_y = 0
        elif y < 0:
            scale_factor = y / min_value
            # Shades of red
            #color = (255 * scale_factor, 0, 0)
            color = np.multiply(scale_factor, BLUE)
        else:
            scale_factor = y / max_value
            # Shades of blue
            #color = (0, 0, 255 * scale_factor)
            color = np.multiply(scale_factor, NEON_PINK)
            
        if graph_type == 'heatmap':
            rect = Rect((10 + 300.0 / constants.NUM_BOXES * x , 100), (300 / constants.NUM_BOXES, 80))
            screen.draw.filled_rect(rect, color)
        elif graph_type == 'scatterplot':
            # Draw a 3x1 Rect because there's no function to draw a pixel
            # y coord is between 100 and 180
            y_coord = int(140 + 40 * -y)
            rect = Rect((10 + 300.0 / constants.NUM_BOXES * x, y_coord), (3, 1))
            screen.draw.filled_rect(rect, color)        
        elif graph_type == 'boxes_ring':
            # Draw lines around an ellipse using polar coordinates
            LINE_LENGTH = 50
            
            # Calculate the offset, used to display absolute values.
            offset = abs_y * LINE_LENGTH / 2
            
            # Calculate the coordinates for the inner end of the line
            r = constants.RING_RADIUS - LINE_LENGTH / 2 + offset
            theta = x / constants.NUM_BOXES * 360
            (inner_x, inner_y) = util.pol2cart(r, theta)
            inner_coords = util.adjust_coords(inner_x, inner_y)
            
            # Calculate the coordinates for the outer end of the line
            r = constants.RING_RADIUS + LINE_LENGTH / 2 + offset
            (outer_x, outer_y) = util.pol2cart(r, theta)
            outer_coords = util.adjust_coords(outer_x, outer_y)
            
            # Finally draw the line
            pygame.draw.line(screen.surface, color, inner_coords, outer_coords, width = 10)

