import csv
import sys
import numpy as np
import os

csv_filename = sys.argv[1]

# Assume there are four channels; they are columns 1-4. 0 is the timestamp.
for channel in range(1, 4 + 1):
    elements_samples = []

    with open(csv_filename, mode='r') as csv_file:
        csv_reader = csv.reader(csv_file)
        
        for row in csv_reader:
            elements_samples.append(float(row[channel]))
    
    min_ = min(elements_samples)
    max_ = max(elements_samples)
    range_ = max_ - min_
    
    console_samples = [int((s - min_) / range_ * 65000) for s in elements_samples]
    cs_array = np.asarray(console_samples, dtype='uint16')
    
    channel_dir_name = f'{csv_filename}_console_channel{channel}'
    if not os.path.exists(channel_dir_name):
        channel_dir = os.makedirs(channel_dir_name)
    cfname = os.path.join(channel_dir_name, 'poredata.bin')
    with open(cfname, mode='w') as console_file:
        cs_array.tofile(console_file)

