WIDTH = 1800
HEIGHT = 900
CENTER = (WIDTH / 2, HEIGHT / 2)

TORUS_THICKNESS = 75

NUM_BOXES = 300

# Maze options.
DRAW_DISTANCES_FROM_MAXINE = False
DRAW_CONTROLS = True
DRAW_GRID = False

# Multiplier for the speed of Maxine and all enemies. 1 is normal speed.
SPEED = 1

# Should this be determined dynamically?
MIN_RMS = 800
MAX_RMS = 4000

NUM_LEVELS = 8

# The speed of moving the voltage knob, in degrees per frame.
VOLTAGE_KNOB_SPEED = 1

# The video file shown in the background.
VIDEO_FILE = None
VIDEO_WIDTH = None
VIDEO_HEIGHT = None

# A tuple containing the number of zombies, snakes and ghosts to produce each
# spike (in that order)
MONSTER_RATIO = (3, 3, 3)
# The number of doors added per spike
DOORS = 10

# The MAC addresses of various consoles.
KENT_MAC = '04e9e50cc5b9'
KENT_OLD_MAC = '04e9e50c6a0b'
JONATHAN_MAC = '04e9e50c6a0b'
NAME2MAC = {'Jonathan': JONATHAN_MAC, 'JustinsBoardFromKent': KENT_MAC,
    'JustinsBoardFromJonathan': '04e9e50cc5ba', 'Hackerboard5': '04e9e50cc5df', 'JustinsOtherBoard': '04e9e50c69f3'}

