import spike_object

def test_separate_spikes_to_arff_string():
    spikes = spike_object.Spikes()
    
    data = [1000,2000,1000]
    mean = 500
    spike = spike_object.Spike(data, mean)
    
    spikes.add_spike(spike)
    
    string = spikes.separate_spikes_to_arff_string()
    print(string)

test_separate_spikes_to_arff_string()

