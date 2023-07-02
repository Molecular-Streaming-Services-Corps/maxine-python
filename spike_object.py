import numpy as np
import os
import math

from util import memoized

class Spike:
    def __init__(self, data, mean):
        '''Create a spike based on the data for the spike and the mean at the
        time of the spike. The data is the height at each sample in the spike
        minus the mean.'''
        self.data = np.array(data, dtype='double')
        self.mean = mean

    @memoized
    def peak(self):
        return int(np.max(self.data))

    @memoized
    def duration(self):
        return int(len(self.data))

    @memoized
    def skewness(self):
        '''Calculate the skewness of the Spike. Returns NaN for spikes of
        length 1.'''
        mean = np.mean(self.data)
        median = np.median(self.data)
        sd = np.std(self.data)
        
        return 3 * (mean - median) / sd

    @memoized
    def kurtosis(self):
        '''Calculates the kurtosis of a 1 dimensional numpy array representing a spike.'''
        sd = np.std(self.data)
        
        moment_4 = np.mean((self.data - np.mean(self.data))**4)
        
        K = moment_4 / sd**4
        return K

    @memoized
    def objectivity(self):
        '''Calculates a/b, where a is the time before the peak and b is the time
        after the peak within the duration of the spike.'''
        peak_index = np.argmax(self.data)
        a = peak_index
        b = self.duration() - 1 - peak_index
        
        return a / b

    @memoized
    def time_ten_values(self):
        '''Creates 10 values that correspond to the means of 10 equal parts of
        the spike. If the spike has less than 10 samples, just uses the mean
        sample for all 10 values.
        
        "Vector of one ionic current-time waveform divided into 10 equal parts
        in the time direction."'''
        if self.duration() < 10:
            return [np.mean(self.data)] * 10
        
        sections = np.array_split(self.data, 10)
        values = [np.mean(s) for s in sections]
        
        return values

    @memoized
    def current_twenty_values(self):
        '''Creates 20 values. 10 on each side of the peak. They are divided into
        10 buckets of equal size and the mean of each bucket is used.

        If the spike has less than 10 samples on either side of the peak,
        just uses the mean sample for all 20 values.

        "The vector of one ionic current-time waveform divided into 10
        equal parts in the current direction"
        '''    
        peak_index = np.argmax(self.data)
        
        before = self.data[0 : peak_index]
        after = self.data[peak_index : ]

        if len(before) < 10 or len(after) < 10:
            return [np.mean(self.data)] * 20

        means_before = self.bucketify_section_(before)
        means_after = self.bucketify_section_(after)
        
        means = np.concatenate([means_before, means_after])
        return means

    def bucketify_section_(self, section):
        NUM_BUCKETS = 10
        min_ = np.min(section)
        bucket_size = (np.max(section) - min_) / NUM_BUCKETS
        
        # TODO do more efficiently if necessary
        buckets = [[] for i in range(10)]

        for sample in section:
            location = (sample - min_) // bucket_size
            location = int(location)
            location = min(9, location)
            buckets[location].append(sample)
        
        means = np.zeros(10)
        for i, bucket in enumerate(buckets):
            means[i] = np.mean(bucket)

        return means

class Spikes:
    '''Stores all the spikes in a dataset or live data session.'''
    def __init__(self):
        self._spikes = []
        
    def add_spike(self, spike):
        self._spikes.append(spike)
    
    def save_separate_spikes_as_arff(self, data_dir):
        string = self.separate_spikes_to_arff_string()
    
        filename = os.path.join(data_dir, 'separate_spikes.arff')
        with open(filename, mode='w') as f:
            f.write(string)
    
    def separate_spikes_to_arff_string(self):
        # Make ARFF header
        header = '''
% Auto-generated Molecular Reality file containing separate spikes.
@RELATION spikes

@ATTRIBUTE peak NUMERIC
@ATTRIBUTE duration NUMERIC
@ATTRIBUTE skewness NUMERIC
@ATTRIBUTE kurtosis NUMERIC
@ATTRIBUTE objectivity NUMERIC
'''
        for part in range(1, 10 + 1):
            header += self._make_attribute(f'time{part}', 'NUMERIC')
        for part in range(1, 20 + 1):
            header += self._make_attribute(f'current{part}', 'NUMERIC')
            
        # Make ARFF data section
        data_section = '@DATA\n'
        
        def m(number):
            '''Replace nan and inf with '?'.'''
            if math.isnan(number) or math.isinf(number):
                return '?'
            else:
                return number
        
        for s in self._spikes:
            entry = f'{s.peak()},{s.duration()},{m(s.skewness())},{m(s.kurtosis())},{m(s.objectivity())},{self._list_to_arff(s.time_ten_values())},{self._list_to_arff(s.current_twenty_values())}\n'
            data_section += entry
            
        return f'{header}\n{data_section}'
        
    def _make_attribute(self, name, datatype):
        return f'@ATTRIBUTE {name} {datatype}\n'
        
    def _list_to_arff(self, L):
        out = ''
        for i, value in enumerate(L):
            out += str(i)
            if i != len(L) - 1:
                out += ','
        return out

spikes = Spikes()

