import numpy as np
import logging
import pygame
import time

import util
import constants
import data
import colors

# Set up logger for this module
logger = logging.getLogger('graphs')
logger.setLevel(logging.INFO)
import sys
handler = logging.StreamHandler(sys.stdout)
handler.formatter = logging.Formatter('%(asctime)s  %(name)s %(levelname)s: %(message)s')
logger.addHandler(handler)

class VerticalLineRing:
    '''Draws a vertical-line based signal ring using sample data. It uses
    constants.NUM_BOXES to choose the number of vertical lines on the ring.'''
    def __init__(self, screen, live, num_frames):
        self.screen = screen
        self.samples = []
        self.present_box = 0
        self.line_extent = 25
        
        if live:
            self.frame_size = 5120
        else:
            self.frame_size = 1667

        self.samples_to_show = num_frames * self.frame_size

        # These are in the range from -line_extent to +line_extent.
        # They only go up to the point where data has been provided.
        self.tops = []
        self.bottoms = []

        self.fake_tops = np.random.randint(0, self.line_extent, constants.NUM_BOXES)
        self.fake_bottoms = np.random.randint(-self.line_extent, 0, constants.NUM_BOXES)
    
        self.box_is_spike = [False] * constants.NUM_BOXES
        
        self.amplifier_max = 20000
        self.amplifier_min = -20000
        
    def give_samples(self, samples):
        if not len(samples):
            return
    
        before = time.perf_counter()
    
        #samples = samples.astype('int32')
        self.samples = samples

        maxes, mins = data.Data.calculate_maxes_and_mins(samples, self.frame_size)
        
        #min_ = self.amplifier_min #int(np.min(samples))
        #max_ = self.amplifier_max #int(np.max(samples))
        min_ = int(np.min(samples))
        max_ = int(np.max(samples))
        range_ = max_ - min_ + 1
        
        h = 2*self.line_extent
        self.tops = np.array([- int((v - min_) / range_ * h) for v in maxes])
        self.bottoms = np.array([- int((v - min_) / range_ * h) for v in mins])

        logger.debug('len(self.tops): %s', len(self.tops))
        logger.debug('self.tops: %s', self.tops)
        logger.debug('self.bottoms: %s', self.bottoms)        

        after = time.perf_counter()
        logger.debug('give_samples took %s seconds', after - before)

    def advance_n_frames(self, n):
        # Remove the spikes from boxes that are being overwritten on the graph.
        for i in range(1, n + 1):
            box = (self.present_box + i) % constants.NUM_BOXES
            self.box_is_spike[box] = False
        
        # Advance present_box
        self.present_box = int(self.present_box + n) % constants.NUM_BOXES

    def draw(self):
        before = time.perf_counter()
        # Draw the vertical lines
        num_lines = len(self.tops)
        data_start_box = (self.present_box - num_lines) % constants.NUM_BOXES
        for i in range(0, num_lines):
            brightness = int(255 * i / constants.NUM_BOXES)
            color = (brightness, brightness, 0)
            
            index = (data_start_box + i) % constants.NUM_BOXES
            if self.box_is_spike[index]:
                color = colors.WHITE
            
            top = self.tops[i]
            bottom = self.bottoms[i]
            
            #print(num_lines)
            #if top == self.bottoms[i]:
            #    if num_lines == constants.NUM_BOXES:
            #        import pdb; pdb.set_trace()
            
            angle = ((data_start_box + i) * 360 / constants.NUM_BOXES) % 360
            self.draw_line(angle, top, bottom, color)
        
        # Draw the red line at present_angle
        self.draw_line(self.present_box * 360 / constants.NUM_BOXES, -2*self.line_extent, 0, colors.MEDIUM_RED)
        
        after = time.perf_counter()
        logger.debug('Drawing VLR took %s seconds', after - before)
        
    def draw_line(self, theta, top, bottom, color):
        # Calculate the coordinates for the inner end of the line
        r = constants.RING_RADIUS + top
        (inner_x, inner_y) = util.pol2cart(r, theta)
        inner_coords = util.adjust_coords_ring(inner_x, inner_y)
        
        # Calculate the coordinates for the outer end of the line
        r = constants.RING_RADIUS + bottom
        (outer_x, outer_y) = util.pol2cart(r, theta)
        outer_coords = util.adjust_coords_ring(outer_x, outer_y)
        
        # Finally draw the line. pygame.draw.line has a bug where it makes
        # randomly horizontral or vertical lines.
        #pygame.draw.line(self.screen.surface, color, inner_coords, outer_coords, width = 15)
        self.screen.draw.line(inner_coords, outer_coords, color)
        # For debugging
        #pygame.draw.circle(self.screen.surface, 'white', inner_coords, 1)
        #pygame.draw.circle(self.screen.surface, 'white', outer_coords, 1)

    def add_spike(self):
        '''Sets the box represented by present_box to be a spike.'''
        self.box_is_spike[self.present_box] = True

class SpikeGraph:
    def __init__(self, screen, live):
        '''screen: the pgzero screen object.
        The frame will be the numpy array of current data containing the latest spike'''
        self.screen = screen
        self.frame = None
        self.top_left = (1464, 44)
        self.bottom_right = (1785, 251)
        self.width = self.bottom_right[0] - self.top_left[0]
        self.height = self.bottom_right[1] - self.top_left[1]
        
        # These are in the range from 0 to height, with 0 representing the top
        self.tops = np.zeros(self.width) + 10
        self.bottoms = np.ones(self.width) + 15
    
        if live:
            self.frame_size = 5120
        else:
            self.frame_size = 1667

    def set_frame(self, frame):
        global logger
        w = self.width
        self.frame = frame
        box_width = self.frame_size // w
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
        BOX = pygame.Rect(self.top_left, (self.width, self.height))
        self.screen.draw.filled_rect(BOX, 'black')
        
        l = self.screen.draw.line
        # Draw the lines
        for i in range(0, self.width):
            (left, top) = self.top_left
            x = left + i
            y1 = self.tops[i] + top
            y2 = self.bottoms[i] + top
            
            l((x, y1), (x, y2), 'red')

class ContinuousGraph:
    def __init__(self, screen, live):
        '''screen: the pgzero screen object.
        The frames will be the numpy arrays of current data containing the signal
        that was recorded during each frame of animation.'''
        self.screen = screen

        # Obsolete discrete zoom settings
        ## Time axis zoom settings, measured in seconds
        #self.time_settings = [1, 10, 20, 50, 100]
        self.lilith_fps = 20
        #self.change_time_setting(0)
        # The number of frames to keep. This has to be the maximum
        # ever shown at once.
        self.change_time_setting_continuous(1.0)
        self.frames_to_keep = 100 * self.lilith_fps 
        self.last_frames = []

        self.top_left = (1464, 44)
        self.bottom_right = (1785, 251)
        self.width = self.bottom_right[0] - self.top_left[0]
        self.height = self.bottom_right[1] - self.top_left[1]

        self.zoom_current_axis(1)
        
        # These are in the range from 0 to height, with 0 representing the top
        self.tops = np.zeros(self.width) + 10
        self.bottoms = np.ones(self.width) + 15
        self.middles = np.zeros(self.width) + 13
        
        if live:
            self.frame_size = 5120
        else:
            self.frame_size = 1667
    
    def change_time_setting_continuous(self, seconds):
        if seconds > 0 and seconds <= 100:
            self.time_setting = seconds
            self.n_frames = int(seconds * self.lilith_fps)
   
    def zoom_current_axis(self, scale):
        if scale > 0 and scale < self.height:
            self.zoom_scale = scale
   
    def change_time_setting(self, index):
        '''Obsolete discrete zoom function'''
        lilith_fps = 20
        
        if index >= 0 and index < len(self.time_settings) - 1:
            self.time_settings_index = index
            self.n_frames = self.time_settings[index] * self.lilith_fps
    
    def set_frame(self, frame):
        global logger
        
        # Add it to the end of last_six_frames
        if len(self.last_frames) < self.frames_to_keep:
            self.last_frames.append(frame)
        else:
            self.last_frames = self.last_frames[1:] + [frame]
        
        last_n_frames = self.last_frames[-self.n_frames:]
        
        all_data = np.concatenate(last_n_frames)
        
        w = self.width
        self.frame = frame
        box_width = (self.frame_size * len(last_n_frames)) // w
        num_boxes = w
        
        maxes = np.zeros(num_boxes)
        mins = np.zeros(num_boxes)
        medians = np.zeros(num_boxes)
        
        #for i in range(0, box_width):
        for i in range(0, num_boxes):
            box_start = box_width * i
            box_end = box_width * (i + 1)
            values = all_data[box_start : box_end]
            
            maxes[i] = values.max()
            mins[i] = values.min()
            medians[i] = np.median(values)
            
        max_ = maxes.max()
        min_ = mins.min()
        range_ = max_ - min_

        h = self.height
        
        mean_ = np.mean(all_data)
        vertical_center = h / 2
        
        self.tops = np.array([vertical_center - int((v - mean_) / range_ * vertical_center * self.zoom_scale) for v in maxes])
        self.bottoms = np.array([vertical_center - int((v - mean_) / range_ * vertical_center * self.zoom_scale) for v in mins])
        self.middles = np.array([vertical_center - int((v - mean_) / range_ * vertical_center * self.zoom_scale) for v in medians])
        
        # Handle zooming while making sure that lines don't go off the edge of the TV
        self.tops = np.maximum(0, np.minimum(h,  self.tops))
        self.bottoms = np.maximum(0, np.minimum(h, self.bottoms))
        self.middles = np.maximum(0, np.minimum(h, self.middles))        
    
    def draw(self):
        BOX = pygame.Rect(self.top_left, (self.width, self.height))
        self.screen.draw.filled_rect(BOX, 'black')
        
        l = self.screen.draw.line
        # Draw the lines
        for i in range(0, self.width):
            (left, top) = self.top_left
            
            # Draw the main vertical line
            x = left + i
            y1 = self.tops[i] + top
            y2 = self.bottoms[i] + top
            
            l((x, y1), (x, y2), 'green')
            
            # Draw the median line in the middle of it
            my1 = self.middles[i] + 2 + top
            my2 = self.middles[i] - 2 + top
            
            l((x, my1), (x, my2), 'white')
            
            #print(y1, y2, my1, my2)

def draw_graph(i, d, graph_type, screen, STANDALONE):
    # Draw a rectangle behind the graph
    if graph_type not in ['boxes_ring','line_ring']:
        BOX = Rect((9, 99), (302, 82))
        screen.draw.filled_rect(BOX, colors.MEDIUM_GREEN)
    
    # Neon pink is positive and grape is negative
    
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
            color = colors.WHITE
            abs_y = 0
        elif x == 0:
            # A black line at the origin
            color = colors.MEDIUM_RED
            abs_y = 0
        elif y < 0:
            scale_factor = y / min_value
            # Shades of red
            #color = (255 * scale_factor, 0, 0)
            color = np.multiply(scale_factor, colors.BLUE)
        else:
            scale_factor = y / max_value
            # Shades of blue
            #color = (0, 0, 255 * scale_factor)
            color = np.multiply(scale_factor, colors.NEON_PINK)
            
        if graph_type == 'heatmap':
            rect = Rect((10 + 300.0 / constants.NUM_BOXES * x , 100), (300 / constants.NUM_BOXES, 80))
            screen.draw.filled_rect(rect, color)
        elif graph_type == 'scatterplot':
            # Draw a 3x1 Rect because there's no function to draw a pixel
            # y coord is between 100 and 180
            y_coord = int(140 + 40 * -y)
            rect = Rect((10 + 300.0 / constants.NUM_BOXES * x, y_coord), (3, 1))
            screen.draw.filled_rect(rect, color)

torus_image = None
def draw_torus(screen, images):
    global torus_image
    if not torus_image:
        #image_width = 629
        #image_height = 470
        scale = (constants.TORUS_OUTER_WIDTH, constants.TORUS_OUTER_HEIGHT)
        
        surf = images.torus
        torus_image = pygame.transform.scale(surf, scale)
        
    left = constants.CENTER[0] - constants.TORUS_OUTER_WIDTH // 2
    top = constants.CENTER[1] - constants.TORUS_OUTER_HEIGHT // 2
    screen.blit(torus_image, (left, top))

