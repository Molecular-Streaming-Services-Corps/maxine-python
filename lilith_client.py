# Installed package.
import websocket

# Builtin packages
import json
import struct
import binascii
from threading import Timer, Thread
import time
import queue
import numpy as np

# Enable websocket logging of exceptions
import logging
wslogger = logging.getLogger('websocket')
wslogger.setLevel(logging.INFO)
wslogger.addHandler(logging.StreamHandler())

# Set up logger for this module
logger = logging.getLogger('lilith_client')
logger.setLevel(logging.INFO)
import sys
handler = logging.StreamHandler(sys.stdout)
handler.formatter = logging.Formatter('%(asctime)s  %(name)s %(levelname)s: %(message)s')
logger.addHandler(handler)

# Must set the root logger to debug or info to allow messages to show
logging.getLogger().setLevel(logging.DEBUG)

# Local packages.
import util
import struct_definitions

PROTOCOL = 'ws://' # Lilith doesn't use HTTPS
HOST = 'lilith.demonpore.tv:3000/'
KENT_MAC = '04e9e50cc5b9'
KENT_OLD_MAC = '04e9e50c6a0b'
JONATHAN_MAC = '04e9e50c6a0b'
MAC = JONATHAN_MAC
NAME2MAC = {'Jonathan': JONATHAN_MAC, 'Kent': KENT_MAC}

def setup():
    global PATH
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
q = queue.Queue()
state_q = queue.Queue()
ws = None
ws_connected = False

sample_index = 0
SAMPLES_PER_SECOND = 10**5
samples_per_packet = int(SAMPLES_PER_SECOND / 60) + 1

def on_open(ws):
    global ws_connected, logger
    logger.info('Connected succesfully')
    
    get_metadata('version', ws)
    get_metadata('bias_settings_history', ws)

    set_game_subscription(ws)
    logger.debug('Completed set_game_subscription')
    
    ping(ws)
    logger.debug('Started ping')
    
    request_data(ws, 1)
    logger.debug('Requested data')
    
    ws_connected = True


def on_message(wsapp, message):
    global logger
    
    # Necessary to get the traceback and not just the error type and info
    try:
        logger.debug('Message received: %s', message[:10])
        code = get_typecode(message)
        logger.debug('Message typecode: %s', code)
        process_message(code, message)
    except Exception:
        import traceback
        logger.error(traceback.format_exc())

#def on_close(ws, close_status_code, close_msg):
def on_close(ws, close_status_code, close_msg):
    global ws_connected
    #print(f"WebSocket closed with code {close_status_code} and message: {close_msg}")
    print('WebSocket closed!')

    ws_connected = False
    
def main():
    global q, ws, logger

    URI = PROTOCOL + HOST + PATH
    logger.info('URI: ' + URI)

    logger.info('Connecting to websocket')
    wsapp = websocket.WebSocketApp(URI, header=HEADERS, on_message=on_message,
         on_open=on_open, on_close=on_close)
    ws = wsapp
    wsapp.run_forever()

def get_typecode(message):
    '''Get the typecode of a binary message from Lilith.
    message is a bytes object and the big-endian uint16 at the start is the typecode.'''
    ## The extra c's are because the format string has to cover every byte of the data.
    s = struct.Struct('!H') #+ 'c' * (len(message) - 2))
    data = s.unpack(message[0 : 2])
    return data[0]
    
def process_message(code, message):
    global pressed, channel, q, state_q, logger

    # typecode 0: update
    if code == 0:
        logger.debug('[0] Current data update received')
        if len(message) < 3000:
            logger.debug('Empty current data message.')
        else:
            data = SampleData(message)
            logger.debug('process_message: sample count: %s', data.sample_count)
            # Maybe the empty current data message gives you a false channel
            #print('process_message: found out channel:', data.channel)
            #channel = data.channel
            
            q.put(data)
         
    # typecode 1: WEBSOCK_JSON_DATA
    elif code == 1:
        logger.debug('[1] JSON data received.')
        json_string = message[2:].decode('unicode_escape')
        logger.debug('process_message: %s', json_string)
        data = json.loads(json_string)
        metadata.update(data)
        logger.debug('process message: all metadata: %s', metadata)
    # typecode 104: WEBSOCK_DEVICE_CLOSED
    elif code == 104:
        logger.info('[104] Device is closed.')
    # typecode 107: WEBSOCK_NEW_JOYSTICK
    elif code == 107:
        # The joystick data is a uint16 in big-endian with bits to represent what's pressed.
        s = struct.Struct('!H')
        unpacked_tuple = s.unpack(message[2:4])
        joystick_data = unpacked_tuple[0]
        logger.debug('process_message: raw joystick data: %s', joystick_data)
        pressed = util.process_joystick_data(joystick_data)
        logger.debug('process_message: joystick used: %s', pressed)
        data = JoystickData(pressed)
        q.put(data)
    # typecode 20: WEBSOCK_STATE
    elif code == 20:
        json_string = message[2:].decode('ascii') 
        status_data = StatusData(json_string)
        state_q.put(status_data)

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
        
        # Old possibly slow code to extract 1667 int16's with struct instead of numpy 
        # It also created a tuple which may be slower than a numpy array for later code
        #samples_bytes = message[16:]
        #s = struct_definitions.numbers_1667
        #self.samples = s.unpack(samples_bytes)
        dt = np.dtype(np.int16)
        dt = dt.newbyteorder('>')
        self.samples = np.frombuffer(message, dtype=dt, offset=16)
        
        logger.debug('samples: %s %s', len(self.samples), self.samples[0 : 10])
        
        #print('SampleData self.websock_type, self.channel, self.stride, self.start, self.end:',
        #      self.websock_type, self.channel, self.stride, self.start, self.end) 

class JoystickData:
    def __init__(self, pressed):
        self.pressed = pressed

class StatusData:
    def __init__(self, json_string):
        self.json_string = json_string

def consume_samples():
    '''Optional loop in a separate thread. It simulates the game loop. It
    waits a 60th of a second and then pops any items on the queue (global
    varialbe q). This function is only used in demo mode (running lilith_client
    as a program. When lilith_client is used as a library you can use your own
    game loop.'''
    global q, state_q

    while True:
        d_list = consume_latest_samples(q)
        
        for i, data in enumerate(d_list):
            if isinstance(data, SampleData):
                logger.info('(%s) consume_samples gets SampleData with start: %s',
                        i, data.start)
            elif isinstance(data, JoystickData):
                logger.info('(%s) consume_samples gets JoystickData with pressed: %s',
                        i, data.pressed)
        
        state_d_list = consume_latest_samples(state_q)
        
        for i, data in enumerate(state_d_list):
            if isinstance(data, StatusData):
                logger.info('(%s) consume_samples gets StatusData from player, starting with: %s',
                      i, data.json_string[0 : 50])
        
        time.sleep(1.0 / 60.0)

def consume_latest_samples(q):
    '''A non-blocking function that returns a list of any SampleData/
    JoystickData/StatusData objects that are on the queue (and removes them 
    from the queue).'''
    sd_list = []

    while True:
        try:
            sample_data = q.get(False)
            sd_list.append(sample_data)  
            # If `False`, the program is not blocked. `Queue.Empty` is thrown if 
            # the queue is empty
        except queue.Empty:
            return sd_list
    

def get_metadata(key, ws):
    format_string = '!HH' + ('s' * len(key))
    print('get_metadata:', format_string)
    s = struct.Struct(format_string)
    data = [1, 0] + [c.encode('ascii') for c in key]
    print('get_metadata:', data)
    packed_data = s.pack(*data)
    print('get_metadata:', packed_data, type(packed_data))
    ws.send(packed_data, websocket.ABNF.OPCODE_BINARY)
    return None

# Ping stuff
def setup_ping(ws):
    t = Timer(0.2, run_ping, (ws,))
    t.start()

def run_ping(ws):
    ping(ws)

def ping(ws):
    s = struct.Struct('!H')
    # message type 100 is PING
    packed_data = s.pack(100)
    ws.send(packed_data, websocket.ABNF.OPCODE_BINARY)
    
    setup_ping(ws)
    return None
    
# Subscribing to games
def set_game_subscription(ws):
    subscribe_data(ws, 2, UUID, 0, 2048, 0)

def subscribe_data(ws, id, mac, file_id, stride, filter):
    # Subscribe code = 102
    # Subscription ID (returned in all data packets)
    # Device mac address
    # File ID
    # Stride
    # Filter
    s = struct.Struct('!HL6sLLL')
    data = [102, id, mac, file_id, stride, filter]
    packed_data = s.pack(*data)
    ws.send(packed_data, websocket.ABNF.OPCODE_BINARY)
    
    return None

# Requesting data.
def request_data(ws, sample_stride):
    global sample_index, samples_per_packet

    # Start code = 12
    # Device id (0 now)
    # Channel
    # sample length
    # sample_start_high
    # sample_start_low
    # sample_stride
    s = struct.Struct('!HHHlLLL')
    data = [12, INDEX, channel, samples_per_packet, 0, sample_index, sample_stride]
    packed_data = s.pack(*data)
    ws.send(packed_data, websocket.ABNF.OPCODE_BINARY)
    
    sample_index += samples_per_packet
    setup_request_data(ws, sample_stride)
    return None

def setup_request_data(ws, sample_stride):
    t = Timer(1.0 / 60, run_request_data, (ws, sample_stride))
    t.start()

def run_request_data(ws, sample_stride):
    request_data(ws, sample_stride)

# Setting bias
def set_bias(bias_mv : float):
    global ws, ws_connected
    if ws and ws_connected:
        # Bias code = 2
        # Device = 0
        s = struct.Struct('!HHf')
        data = [2, 0, bias_mv / 1000]
        packed_data = s.pack(*data)
        ws.send(packed_data, websocket.ABNF.OPCODE_BINARY)

# Moving the syringe
def move_pump(steps: int, delay: int):
    global ws, ws_connected, logger
    if ws and ws_connected:
        #logger.info('move_pump %s %s', steps, delay)
        # Pump code = 29 : uint16
        # steps : int32
        # delay : uint32
        s = struct.Struct('!HiI')
        data = [29, steps, delay]
        packed_data = s.pack(*data)
        ws.send(packed_data, websocket.ABNF.OPCODE_BINARY)
    else:
        logger.warning('move_pump called when websocket is disconnected')

# Sending the status of one player's game in Maxine vs the uMonsters. Only starts after the socket is open.
def send_status(json_string):
    global ws, ws_connected
    if ws and ws_connected:
        # Status code = 20 : uint16
        # Just stick the JSON data on
        s = struct.Struct('!H')
        data = [20]
        packed_data = s.pack(*data)

        json_bytes = bytes(json_string, 'ascii')
        #print('send_status: json_bytes:', json_bytes)
        packed_data = packed_data + json_bytes
        
        try:
            ws.send(packed_data, websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            logger.error('Exception sending status: type: %s', type(e))

def set_metadata(key, json_string):
    global ws, ws_connected
    if ws and we_connected:
        # Set metadata code = 21 : uint16
        s = struct.Struct('!H')
        data = [21]
        packed_data = s.pack(*data)
        
        # Add a null terminator to separate the two strings.
        key = key + '\0'
        
        packed_data = packed_data + bytes(key, 'ascii') + bytes(json_string, 'ascii')
        
        ws.send(packed_data, websocket.ABNF.OPCODE_BINARY)

if __name__ == '__main__':
    setup()

    # Run the interaction loop in another thread
    t = Thread(target=main)
    t.start()
    
    # Run this in the main thread
    consume_samples()
    
