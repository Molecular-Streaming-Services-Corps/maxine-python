import asyncio
import websockets
import json
import struct
import binascii
from threading import Timer

import util

PROTOCOL = 'ws://' # Lilith doesn't use HTTPS
HOST = 'lilith.demonpore.tv:3000/'
MAC = '04e9e50cc5b9'
PATH = 'game/' + MAC + '/' + 'session'

# Set up authorization. It doesn't matter what the password is.
# From wikipedia: if the browser uses Aladdin as the username and open sesame as the password, then the field's value is the Base64 encoding of Aladdin:open sesame, or QWxhZGRpbjpvcGVuIHNlc2FtZQ==.
# Authorization: Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ== 
HEADERS = {'Authorization': 'Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ=='}

UUID = b'\x04\xe9\xe5\x0c\xc5\xb9' # Seems to be the MAC address of Hackerboard.

# For Player 3. Might be arbitrary. Included in all received packets.
INDEX = 2

metadata = {}
pressed = []
channel = 0

async def main():
    URI = PROTOCOL + HOST + PATH
    print('URI: ' + URI)

    print('Connecting to websocket')
    async with websockets.connect(URI, extra_headers = HEADERS) as ws:
        print('Connected succesfully')
        #await ws.send("Hello world!")
        #await ws.recv()
        
        # Doesn't seem to get a response :( Might be obsolete.
        await get_metadata('version', ws)
        await get_metadata('bias_settings_history', ws)
        
        await set_game_subscription(ws)
        print('Completed set_game_subscription')
        await ping(ws)
        print('Started ping')
        
        # Might be obsolete.
        await request_data(ws, 0, 15000, 1)
        print('Requested data')
        
        async for message in ws:
            print('Message received:', message)
            code = get_typecode(message)
            print('Message typecode:', code)
            process_message(code, message)

def get_typecode(message):
    '''Get the typecode of a binary message from Lilith.
    message is a bytes object and the big-endian uint16 at the start is the typecode.'''
    ## The extra c's are because the format string has to cover every byte of the data.
    s = struct.Struct('!H') #+ 'c' * (len(message) - 2))
    data = s.unpack(message[0 : 2])
    return data[0]
    
def process_message(code, message):
    global pressed, channel

    # typecode 0: update
    if code == 0:
        print('[0] Current data update received')
        data = SampleData(message)
        print('process_message: sample count:', data.sample_count)
        # Maybe the empty current data message gives you a false channel
        #print('process_message: found out channel:', data.channel)
        #channel = data.channel
         
    # typecode 1: WEBSOCK_JSON_DATA
    elif code == 1:
        print('[1] JSON data received.')
        json_string = message[2:].decode('unicode_escape')
        print('process_message:', json_string)
        data = json.loads(json_string)
        metadata.update(data)
        print('process message: all metadata:', metadata)
    # typecode 104: WEBSOCK_DEVICE_CLOSED
    elif code == 104:
        print('[104] Device is closed.')
    # typecode 107: WEBSOCK_NEW_JOYSTICK
    elif code == 107:
        # The joystick data is a uint16 in big-endian with bits to represent what's pressed.
        s = struct.Struct('!H')
        unpacked_tuple = s.unpack(message[2:4])
        joystick_data = unpacked_tuple[0]
        print('process_message: raw joystick data:', joystick_data)
        pressed = util.process_joystick_data(joystick_data)
        print('process_message: joystick used:', pressed)

class SampleData:
    '''self.start is equivalent to a uint64. It's broken into start_high for the high bits
    and start_low for the low bits.'''
    def __init__(self, message):
        format_string = '!HHIII'
        s = struct.Struct(format_string)
        u = s.unpack(message[0:16])
    
        self.sample_count = (len(message) - 16) // 2
        self.websock_type, self.channel, self.stride, self.start_high, self.start_low = u
        
        self.start = (self.start_high << 32) | self.start_low
        self.end = self.start + self.stride * self.sample_count
        
        self.samples = message[16:]

async def get_metadata(key, ws):
    format_string = '!HH' + ('s' * len(key))
    print('get_metadata:', format_string)
    s = struct.Struct(format_string)
    data = [1, 0] + [c.encode('ascii') for c in key]
    print('get_metadata:', data)
    packed_data = s.pack(*data)
    print('get_metadata:', packed_data, type(packed_data))
    await ws.send(packed_data)
    return None

# Ping stuff
def setup_ping(ws):
    t = Timer(0.2, run_ping, (ws,))
    t.start()

def run_ping(ws):
    asyncio.run(ping(ws))

async def ping(ws):
    s = struct.Struct('!H')
    # message type 100 is PING
    packed_data = s.pack(100)
    await ws.send(packed_data)
    
    setup_ping(ws)
    return None
    
# Subscribing to games
async def set_game_subscription(ws):
    await subscribe_data(ws, 2, UUID, 0, 2048, 0)

async def subscribe_data(ws, id, mac, file_id, stride, filter):
    # Subscribe code = 102
    # Subscription ID (returned in all data packets)
    # Device mac address
    # File ID
    # Stride
    # Filter
    s = struct.Struct('!HL6sLLL')
    data = [102, id, mac, file_id, stride, filter]
    packed_data = s.pack(*data)
    await ws.send(packed_data)
    
    return None

# Requesting data.
async def request_data(ws, sample_start_low, sample_length, sample_stride):
    # Start code = 12
    # Device id (0 now)
    # Channel
    # sample length
    # sample_start_high
    # sample_start_low
    # sample_stride
    s = struct.Struct('!HHHlLLL')
    data = [12, INDEX, channel, sample_length, 0, sample_start_low, sample_stride]
    packed_data = s.pack(*data)
    await ws.send(packed_data)
    
    return None

if __name__ == '__main__':
    asyncio.run(main())
    
