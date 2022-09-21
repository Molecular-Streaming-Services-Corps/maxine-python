'''A module that makes music out of the nanopore's current signal. Presently
it just converts the current level into frequency. But fancier effects can
be added.'''
import numpy as np
import pygame

def current_to_volume(current_data):
    current_data *= 5
    
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

pygame.mixer.quit()
pygame.mixer.init(frequency=100000, channels=1)

