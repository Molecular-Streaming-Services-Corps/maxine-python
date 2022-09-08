import numpy as np

def test_reading_int16s():
    message = b'\x01\x02\x03\x04'

    dt = np.dtype(np.int16)
    dt = dt.newbyteorder('>')
    samples = np.frombuffer(message, dtype=dt)

    print(samples[0] == 258)
    print(samples[1] == 772)
    
if __name__ == '__main__':
    test_reading_int16s()

