import data

def test_find_spikes_in_last_frame():
    '''There was a bug where a lot of spikes have duration exactly
    300 and never above that. This test makes a spike with duration
    500.'''
    samples = []
    for box in range(0, 499):
        contents = [0, 1] * 250
        samples += contents
    
    contents = [501] * 500
    samples += contents
    
    spikes = data.Data.find_spikes_in_last_frame(samples, 500)
    print(len(spikes) == 1)
    if len(spikes) > 0:
        s = spikes[0]
        print(f'Peak: {s.peak()} Duration: {s.duration()} Mean: {s.mean}')
    
test_find_spikes_in_last_frame()
