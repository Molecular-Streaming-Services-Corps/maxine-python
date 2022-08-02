import struct

'''A Struct to extract 1667 signed int16s from a bytes object.'''
numbers_1667 = struct.Struct('!' + 'h' * 1667)

