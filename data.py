import numpy as np
import json
import os

class Data:
    def __init__(self, num_boxes):
        self.num_boxes = num_boxes
        self.current_data = []
        self.joystick_data = []
        self.sample_rate = 10**5
        self.current_frame = 0
        self.init_boxes()
    
    def init_boxes(self):
        self.boxes = [0] * self.num_boxes    
    
    def load_files(self, data_dir):
        # Load current data
        filename = os.path.join(data_dir, 'poredata.bin')
        self.current_data = np.fromfile(filename, 'int16')
    
        # Load joystick data
        meta_filename = os.path.join(data_dir, 'meta.json')
        meta_file = open(meta_filename)
        settings = json.load(meta_file)
        
        if 'joystick' in settings:
            self.joystick_data = settings['joystick']
            
    def get_one_frame_current(self):
        samples_per_frame = self.sample_rate // 60
        
        start = samples_per_frame * self.current_frame
        end = samples_per_frame * (self.current_frame + 1)
        
        cd = self.current_data[start : end]
        if len(cd) > 0:
            frame_current = np.min(cd)
            
            self.boxes = self.boxes[1:] + [frame_current]
        else:
            self.init_boxes()
        
        return None
        
    def get_one_frame_joystick(self):
        # If we are past the end of the data, the joystick isn't being used.
        if self.current_frame > len(self.current_data):
            return 65535
    
        # First find the sample index, then use it to look up the most recent
        # joystick update before that index.
        samples_per_frame = self.sample_rate // 60        
        current_sample_index = samples_per_frame * self.current_frame
        
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
        self.current_frame += 1
        
