import constants

MAXINE_START = (constants.CENTER[0] + 200, constants.CENTER[1]) #(200, 600)

# Certain levels might use scaling in the future.
MAXINE_INITIAL_SCALE = 0.5
MAXINE_CHANGE_FACTOR = 1.2
'''These will make Maxine win when she is 4x the size (after about 8 hits) or
lose when she is a quarter of the size.'''
MAXINE_WIN_SIZE = 4
MAXINE_LOSE_SIZE = 0.25

class Game:
    def __init__(self, Actor):
        self.maxine_current_scale = 1
        
        maxine = Actor('maxine')
        maxine.images = ['maxine']
        maxine.pos = MAXINE_START
        maxine.alive = True
        maxine.scale = MAXINE_INITIAL_SCALE * self.maxine_current_scale
        self.maxine = maxine
        
        self.pore = Actor('pore')
        self.pore.center = (constants.WIDTH/2, constants.HEIGHT/2)

        self.spiraling_monsters = set()
        self.bouncing_monsters = set()
        self.dead_monsters = set()
        self.maze_monsters = set()
        
        self.projectiles = set()

    def grow_maxine(self):
        self.maxine_current_scale *= MAXINE_CHANGE_FACTOR
        self.maxine.scale = MAXINE_INITIAL_SCALE * self.maxine_current_scale
        
    def shrink_maxine(self):
        self.maxine_current_scale /= MAXINE_CHANGE_FACTOR
        self.maxine.scale = MAXINE_INITIAL_SCALE * self.maxine_current_scale

