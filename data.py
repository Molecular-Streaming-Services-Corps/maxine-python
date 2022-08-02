import numpy as np
import json
import os

class Data:
    def __init__(self):
        self.sample_data = []
        self.joystick_data = []
        self.sample_rate = 10**5
        self.latest_frame = 0

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
    
    def get_scaled_boxes(self):
        '''Get the box values scaled to be from -1 to +1, where -1 represents
        the lowest value in the boxes and +1 represents the highest.'''
        if self.no_more_data:
            return self.boxes # All 0s        
        
        min_v = np.min(self.boxes)
        max_v = np.max(self.boxes)
        range_ = max_v - min_v
        scale = range_ / 2
        mid = min_v + scale
        
        scale == 0.01
        
        ret = [(v - mid) / scale for v in self.boxes]
        
        return ret
        

