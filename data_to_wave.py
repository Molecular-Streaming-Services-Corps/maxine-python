import wave
import argparse
import os
import numpy as np

SAMPLE_RATE = 100000

parser = argparse.ArgumentParser(description='Convert poredata.bin file to wave audio file.')
parser.add_argument('--datadir', action='store')
args = parser.parse_args()

pore_filename = os.path.join(args.datadir, 'poredata.bin')
current_data = np.fromfile(pore_filename, 'int16')

wave_filename = os.path.join(args.datadir, 'poredata-volume.wav')

with wave.open(wave_filename, 'wb') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(SAMPLE_RATE)
    
    wav_file.writeframes(current_data)

def current_to_frequency(current_data):
    pos_values = current_data.astype('int32')
    pos_values += 32768
    pos_values = pos_values // 20 + 100
    
    freqs = np.zeros(7000, dtype='int16')

    for value in pos_values:        
        freqs[value] = 20000
    
    music_data = np.fft.ifft(freqs).real.astype('int16')
    
    return music_data    

wave_filename = os.path.join(args.datadir, 'poredata-frequency.wav')

with wave.open(wave_filename, 'wb') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(SAMPLE_RATE)
    
    aframe_size = SAMPLE_RATE // 60
    num_animation_frames = len(current_data) // aframe_size
    music_aframes = []
    for i in range(0, num_animation_frames):
        start_index = i * aframe_size
        end_index = (i + 1) * aframe_size
        aframe = current_data[start_index : end_index]
        aframe_music_data = current_to_frequency(aframe)
        music_aframes.append(aframe_music_data)
    
    music_data = np.concatenate(music_aframes)
    wav_file.writeframes(music_data)

