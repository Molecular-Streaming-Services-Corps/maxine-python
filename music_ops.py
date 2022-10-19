'''A module that makes music out of the nanopore's current signal. Presently
it just converts the current level into frequency. But fancier effects can
be added.'''
import numpy as np
import pygame

def current_to_volume(current_data):
    # The current data is read-only for some reason; it is a ndarray
    current_data = current_data * 5
    
    sound = pygame.sndarray.make_sound(current_data)

    sound.set_volume(1.0)
    sound.play()

def current_to_frequency(current_data):
    pos_values = current_data.astype('int32')
    pos_values += 32768
    pos_values = pos_values // 20 + 100
    
    freqs = np.zeros(7000, dtype='int16')

    for value in pos_values:        
        freqs[value] = 20000
    
    music_data = np.fft.ifft(freqs).real.astype('int16')
    
    music_data *= 400
    
    sound = pygame.sndarray.make_sound(music_data)

    sound.set_volume(1.0)
    sound.play()

def stats_to_frequency(maxes_mins):
    global sound
    maxes, mins = maxes_mins

    if len(maxes) < 2:
        return None

    # Scale maxes and mins between 0 and 1    
    min_ = int(np.min(mins))
    max_ = int(np.max(maxes))
    range_ = max_ - min_ + 1

    maxes = (maxes - min_) / range_
    mins = (mins - min_) / range_
    
    last_max = maxes[-1]
    last_min = mins[-1]
    
    max_freq = scaled_value_to_freq(last_max)
    min_freq = scaled_value_to_freq(last_min)

    # tone from pgzero doesn't work
    freqs = np.zeros(7000, dtype='int16')
    freqs[max_freq] = 20000
    freqs[min_freq] = 20000

    music_data = np.fft.ifft(freqs).real.astype('int16')
    
    music_data *= 400

    # Stop playing the previous frame's sound
    if sound:
        sound.stop()
            
    sound = pygame.sndarray.make_sound(music_data)

    sound.set_volume(1.0)
    sound.play()


def scaled_value_to_freq(value):
    freq = int(value * 6000 + 100)
    return freq

sound = None

pygame.mixer.quit()
pygame.mixer.init(frequency=100000, channels=1)

