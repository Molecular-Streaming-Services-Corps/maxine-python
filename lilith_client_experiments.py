'''A script that can be changed to automatically run an experiment with Lilith.'''

import lilith_client
from threading import Thread

lilith_client.MAC = '04e9e50c6a09'
lilith_client.setup()

# Run the interaction loop in another thread
t = Thread(target=lilith_client.main)
t.start()

# You can't run this anymore because a global variable is False.
#lilith_client.request_data(lilith_client.ws, 1)

# Test whether subscribe_data is robust.
# stride: int = 1
# lilith_client.subscribe_data(
#     lilith_client.ws, lilith_client.INDEX, bytearray.fromhex(lilith_client.MAC),
#     9, stride, 42)
while lilith_client.ws is None or lilith_client.ws_connected == False:
    import time
    time.sleep(1)

lilith_client.send_status('{')
