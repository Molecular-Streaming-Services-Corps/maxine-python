import numpy as np
import json
import os
import math
import time
import logging

import lilith_client
import util
import constants

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
        self.latest_frame = -1
        #self.amplifier_min = -10000
        self.amplifier_max = 20000
        
    def get_absolute_scaled_boxes(self):
        boxes = self.get_boxes()
        
        asb = np.divide(boxes, self.amplifier_max)
        return asb
    
    def middle_spike_exists(self):
        '''This is supposed to calculate whether a spike exists in the middle box.
        It uses the middle box in case there's a voltage change and the graph moves
        up or down. It's too strict to use. And it's based on the boxes which only
        handle minnimums so they miss some spikes.'''
        sb = self.get_scaled_boxes()
    
        MIDPOINT = self.num_boxes // 2
        BLUE_THRESHOLD = 0.1
        
        blue_enough_boxes = [(v > BLUE_THRESHOLD) for v in sb]
        blue_fraction = self.count_true(blue_enough_boxes) / self.num_boxes
        
        #print('blue_fraction:', blue_fraction)
        
        # If at least 90% of the boxes are brightish blue
        if blue_fraction > 0.7:
            middle_box = sb[MIDPOINT]
            # Find the first part of a red section at the midline. Ignore the
            # later boxes in the same spike.
            if middle_box < -0.1 and sb[MIDPOINT - 1] >= 0:
                return True
        
        return False
        
    def count_true(self, array):
        count = 0
        for b in array:
            if b == True:
                count += 1
        
        return count
        
    @staticmethod
    def calculate_maxes_and_mins(samples):
        samples_to_show = 1667*constants.NUM_BOXES
    
        if not len(samples):
            return ([], [])

        # This represents the number of lines used by the present data
        num_used_lines = int(len(samples) / samples_to_show * constants.NUM_BOXES)
        min_ = int(np.min(samples))
        max_ = int(np.max(samples))
        range_ = max_ - min_ + 1

        maxes = np.zeros(num_used_lines)
        mins = np.zeros(num_used_lines)
        # Used for diagnostics
        averages = np.zeros(num_used_lines)
        
        box_width = samples_to_show // constants.NUM_BOXES
        
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

        logger.debug('means: %s', averages)
        logger.debug('maxes: %s', maxes)
        logger.debug('mins: %s', mins)
        
        return (maxes, mins)

    @staticmethod
    def end_spike_exists(maxes_mins):
        '''Detects whether the final box is a spike (positive or negative).'''
        # The required difference between a box and the previous box to count
        # as a spike
        SPIKE_THRESHOLD = 500
        maxes, mins = maxes_mins
        
        if len(maxes) < 2:
            return False
        
        # We don't want this to be the absolute difference, or we'd detect
        # returns to baseline after a spike as well
        diff_maxes = maxes[-1] - maxes[-2]
        if diff_maxes > SPIKE_THRESHOLD:
            return True
        
        diff_mins = -(mins[-1] - mins[-2])
        if diff_mins > SPIKE_THRESHOLD:
            return True
        
        return False

class LiveData(Data):
    def __init__(self, num_boxes):
        super().__init__()
        self.num_boxes = num_boxes
        # A dictionary mapping from frame index to a SampleData object 
        self.data_frames = {}
        self.pressed = []
        self.latest_spike_frame = None
        self.caught_up = False
        self.num_frames_just_received = 0
        self.recent_frames_contain_spikes = []
        
    def load_received_samples_and_count_spikes(self):
        spikes = 0
        prev_frame = self.latest_frame
        self.recent_frames_contain_spikes = []
    
        d_list = lilith_client.consume_latest_samples(lilith_client.q)
        
        for data in d_list:
            if isinstance(data, lilith_client.SampleData):
                sd_frame_index = data.start // 1667
                self.data_frames[sd_frame_index] = data
                
                # Update the latest frame index. There may be missing frames in
                # between if the frames arrive in the wrong order.
                
                # See if it skips frames (it doesn't)
                if sd_frame_index > self.latest_frame + 1:
                    logger.info('Skipping %s frames', sd_frame_index - self.latest_frame + 1)
                
                if util.all_zeros(data.samples):
                    logger.info('Received frame with all 0s')
                
                if sd_frame_index > self.latest_frame:
                    self.latest_frame = sd_frame_index
                    
                # If we process multiple frames of current data during a frame of animation,
                # we want to notice all the spikes
                #if self.middle_spike_exists():
                #    spikes += 1
                #    self.latest_spike_frame = data.samples
                last_n_frames = self.get_last_n_frames(constants.NUM_BOXES)
                maxes_mins = Data.calculate_maxes_and_mins(last_n_frames)
                if Data.end_spike_exists(maxes_mins):
                    spikes += 1
                    self.latest_spike_frame = data.samples
                    self.recent_frames_contain_spikes.append(True)
                else:
                    self.recent_frames_contain_spikes.append(False)
                    
            elif isinstance(data, lilith_client.JoystickData):
                self.pressed = data.pressed

        self.num_frames_just_received = self.latest_frame - prev_frame

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
            num_real_boxes = self.latest_frame + 1
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
        
            # This will be a float (or not)
            time_difference = int(now) - start_time
            samples_so_far = int(time_difference * 100000)
            
            # Make it a frame
            # The theory behind this line is that a) the sample index is always
            # a multiple of 1667 and b) we need to wait until that frame is finished
            # before we can download it. A slight lag would be ok anyway
            sample_index = samples_so_far // 1667 * 1667 - 1667
            lilith_client.sample_index = sample_index
            
            self.caught_up = True
            
            logger.info('Updated sample_index to: %s', sample_index)

    def get_last_n_frames(self, n):
        '''Returns a Numpy array containing the samples from the last n frames.
        If latest_frame is less than n, return latest_frame frames. Put 0s in
        any empty frames.'''
        # latest_frame + 1 == the number of frames so far
        n = min(n, self.latest_frame + 1)
        frame_size = 1667
        num_samples = n * frame_size
        
        end_frame = self.latest_frame
        start_frame = max(0, end_frame - n + 1)
        
        samples = np.zeros(num_samples, dtype='int16')
        empty_frame = np.zeros(frame_size, dtype='int16')
        
        # samples has indexes from 1667*0 to 1667*NUM_BOXES,
        # i goes from say 7 to 106
        for i in range(start_frame, end_frame):
            #import pdb; pdb.set_trace()
            start = (i - start_frame) * frame_size
            end = (i - start_frame + 1) * frame_size
                        
            if i in self.data_frames:
                data = self.data_frames[i].samples
            else:
                data = empty_frame
                logger.info('Used empty_frame')
            
            samples[start:end] = data
            #logger.info('%s %s %s', samples[start:end].shape, data.shape, (start, end))
        
        if util.all_zeros(samples):
            logger.info('Somehow samples is all 0s in get_last_n_frames')
            logger.info('%s %s %s', num_samples, start_frame, end_frame)

        return samples

    def get_num_frames_just_received(self):
        return self.num_frames_just_received

    def get_recent_frames_contain_spikes(self):
        return self.recent_frames_contain_spikes

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
        
    def get_last_n_samples(self, n):
        '''Return the last n samples up to the present frame. Returns all the
        samples if there are less than n samples'''
        before = time.perf_counter()
        
        samples_per_frame = 1667
        
        start = samples_per_frame * (self.latest_frame + 1) - n
        start = max(start, 0)
        end = samples_per_frame * (self.latest_frame + 1)
        
        cd = self.sample_data[start : end]
        
        after = time.perf_counter()
        logger.debug('get_last_n_samples took %s seconds', after - before)
        
        return cd
        
