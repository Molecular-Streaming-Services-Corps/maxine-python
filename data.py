import numpy as np
import json
import os
import math
import time
import logging

import lilith_client

# Set up logger for this module
logger = logging.getLogger('data')
logger.setLevel(logging.INFO)
import sys
handler = logging.StreamHandler(sys.stdout)
handler.formatter = logging.Formatter('%(asctime)s  %(name)s %(levelname)s: %(message)s')
logger.addHandler(handler)


class Data:
    def __init__(self):
        self.sample_data = []
        self.joystick_data = []
        self.sample_rate = 10**5
        self.latest_frame = 0
        #self.amplifier_min = -10000
        self.amplifier_max = 10000

    def get_absolute_scaled_boxes(self):
        boxes = self.get_boxes()
        
        asb = np.divide(boxes, self.amplifier_max)
        return asb
    
    def middle_spike_exists(self):
        sb = self.get_scaled_boxes()
    
        MIDPOINT = self.num_boxes // 2
        BLUE_THRESHOLD = 0.5
        
        blue_enough_boxes = [(v > BLUE_THRESHOLD) for v in sb]
        blue_fraction = self.count_true(blue_enough_boxes) / self.num_boxes
        
        #print('blue_fraction:', blue_fraction)
        
        # If at least 90% of the boxes are brightish blue
        if blue_fraction > 0.9:
            middle_box = sb[MIDPOINT]
            # Find the first part of a red section at the midline. Ignore the
            # later boxes in the same spike.
            if middle_box < -0.5 and sb[MIDPOINT - 1] >= 0:
                return True
        
        return False
        
    def count_true(self, array):
        count = 0
        for b in array:
            if b == True:
                count += 1
        
        return count
        
class LiveData(Data):
    def __init__(self, num_boxes):
        super().__init__()
        self.num_boxes = num_boxes
        # A dictionary mapping from frame index to a SampleData object 
        self.data_frames = {}
        self.pressed = []
        self.latest_spike_frame = None
        self.caught_up = False
        
    def load_received_samples_and_count_spikes(self):
        spikes = 0
    
        d_list = lilith_client.consume_latest_samples(lilith_client.q)
        
        for data in d_list:
            if isinstance(data, lilith_client.SampleData):
                sd_frame_index = data.start // 1667
                self.data_frames[sd_frame_index] = data
                
                # Update the latest frame index. There may be missing frames in
                # between if the frames arrive in the wrong order.
                if sd_frame_index > self.latest_frame:
                    self.latest_frame = sd_frame_index
                    
                # If we process multiple frames of current data during a frame of animation,
                # we want to notice all the spikes
                if self.middle_spike_exists():
                    spikes += 1
                    self.latest_spike_frame = data.samples
            elif isinstance(data, lilith_client.JoystickData):
                self.pressed = data.pressed

        return spikes

    def get_one_frame_joystick(self):
        '''This isn't called by Live Mode.'''
        return 65535

    def get_boxes(self):
        '''Return a list of the min values for the last 100 frames. If there
        are less than 100 frames, or if any frame is missing, insert 0 values.
        A frame in this method is a SampleData object corresponding to a
        particular frame of gameplay.'''
        if self.latest_frame < 100:
            num_real_boxes = self.latest_frame
            padding = [-1, 1] + [0] * (98 - num_real_boxes)
        else:
            num_real_boxes = 100
            padding = []
        
        real_boxes = np.zeros(num_real_boxes)
        for box_id in range(0, num_real_boxes):
            offset = 100 - box_id - 1
            
            frame_id = self.latest_frame - offset
            # Handle missing frames
            if frame_id in self.data_frames:
                df = self.data_frames[frame_id].samples
            else:
                df = [0]
                
            # Set the box to the min value in this frame
            real_boxes[box_id] = np.min(df)
            
        if len(padding) > 0:
            ret = np.concatenate([padding, real_boxes])
        else:
            ret = real_boxes
        #print('get_boxes:', ret)
        return ret

    def get_scaled_boxes(self):
        '''Get the box values scaled to be from -1 to +1, where -1 represents
        the lowest value in the boxes and +1 represents the highest.
        
        TODO: remove code duplication'''
        global logger
        
        min_v = np.min(self.get_boxes())
        max_v = np.max(self.get_boxes())
        range_ = max_v - min_v
        scale = range_ / 2
        mid = min_v + scale
        
        scale += 1
        
        logger.debug('boxes: %s', self.get_boxes())
        # Pre-numpy code
        #ret = [(v - mid) / scale for v in self.get_boxes()]
        # Numpy code
        ret = (self.get_boxes() - mid) / scale
        logger.debug('get_scaled_boxes before nan check: %s', ret)
        ret = [v if not math.isnan(v) else 0 for v in ret]
        logger.debug('get_scaled_boxes after nan check: %s', ret)
        
        
        return ret

    def get_frame(self):
        if self.latest_frame in self.data_frames:
            ret = self.data_frames[self.latest_frame].samples
            return ret
        else:
            return None

    def get_latest_spike_frame(self):
        '''This is only called when there has been a spike'''
        return self.latest_spike_frame

    def try_to_catch_up(self):
        if self.caught_up:
            return
            
        now = time.time()
        md = lilith_client.metadata
        if 'start_time' in md:
            start_time = md['start_time']
        
        # This will be a float
        time_difference = now - start_time
        samples_so_far = int(time_difference * 100000)
        
        # Make it a frame
        sample_index = samples_so_far // 1667 * 1667
        lilith_client.sample_index = sample_index
        
        self.caught_up = True

class PrerecordedData(Data):
    def __init__(self, num_boxes):
        super().__init__()
        self.num_boxes = num_boxes
        self.init_boxes()
        self.no_more_data = False
    
    def init_boxes(self):
        self.boxes = [0] * self.num_boxes    
    
    def load_files(self, data_dir):
        # Load current data
        filename = os.path.join(data_dir, 'poredata.bin')
        self.sample_data = np.fromfile(filename, 'int16')
    
        # Load joystick data
        meta_filename = os.path.join(data_dir, 'meta.json')
        meta_file = open(meta_filename)
        settings = json.load(meta_file)
        
        if 'joystick' in settings:
            self.joystick_data = settings['joystick']
            
    def get_one_frame_current(self):
        samples_per_frame = self.sample_rate // 60
        
        start = samples_per_frame * self.latest_frame
        end = samples_per_frame * (self.latest_frame + 1)
        
        cd = self.sample_data[start : end]
        if len(cd) > 0:
            frame_current = np.min(cd)
            
            self.boxes = self.boxes[1:] + [frame_current]
        else:
            self.init_boxes()
            self.no_more_data = True
        
        return None
    
    def get_one_frame_joystick(self):
        # If we are past the end of the data, the joystick isn't being used.
        if self.latest_frame > len(self.sample_data):
            return 65535
    
        # First find the sample index, then use it to look up the most recent
        # joystick update before that index.
        samples_per_frame = self.sample_rate // 60        
        current_sample_index = samples_per_frame * self.latest_frame
        
        #indexes = [update[0] for update in self.joystick_data]
        
        # The metadata doesn't specify an initial setting for the joystick.
        # This setting means no buttons pressed on either joystick.
        # Some of the bits are ignored and are supposed to be 0, but that's ok.
        last_value = 65535
        
        for index, controls in self.joystick_data:
            if index > current_sample_index:
                break
            else:
                last_value = controls
        
        return last_value
    
    def advance_frame(self):
        self.latest_frame += 1
    
    def get_boxes(self):
        return self.boxes
    
    def get_scaled_boxes(self):
        '''Get the box values scaled to be from -1 to +1, where -1 represents
        the lowest value in the boxes and +1 represents the highest.'''
        if self.no_more_data:
            return self.get_boxes() # All 0s        
        
        min_v = np.min(self.get_boxes())
        max_v = np.max(self.get_boxes())
        range_ = max_v - min_v
        scale = range_ / 2
        mid = min_v + scale
        
        scale == 0.01
        
        ret = [(v - mid) / scale for v in self.get_boxes()]
        
        return ret

    def get_frame(self):
        samples_per_frame = self.sample_rate // 60
        
        start = samples_per_frame * self.latest_frame
        end = samples_per_frame * (self.latest_frame + 1)
        
        cd = self.sample_data[start : end]

        return cd
