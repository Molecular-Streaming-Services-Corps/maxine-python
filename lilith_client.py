import asyncio
import websockets
import json
import struct
import binascii
from threading import Timer

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

async def main():
    URI = PROTOCOL + HOST + PATH
    print('URI: ' + URI)

    print('Connecting to websocket')
    async with websockets.connect(URI, extra_headers = HEADERS) as ws:
        print('Connected succesfully')
        # convert to Python:  webSocket.binaryType = 'arraybuffer';
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
            await print('Message received:', message)

async def get_metadata(key, ws):
    format_string = 'HH' + ('s' * len(key))
    print('get_metadata:', format_string)
    s = struct.Struct(format_string)
    data = [1, 0] + [c.encode('ascii') for c in key]
    print('get_metadata:', data)
    packed_data = s.pack(*data)
    await ws.send(packed_data)
    return None

# Ping stuff
def setup_ping(ws):
    t = Timer(0.2, run_ping, (ws,))
    t.start()

def run_ping(ws):
    asyncio.run(ping(ws))

async def ping(ws):
    s = struct.Struct('H')
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
    s = struct.Struct('HL6sLLL')
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
    s = struct.Struct('HHHlLLL')
    data = [12, INDEX, 0, sample_length, 0, sample_start_low, sample_stride]
    packed_data = s.pack(*data)
    await ws.send(packed_data)
    
    return None

if __name__ == '__main__':
    asyncio.run(main())
    
