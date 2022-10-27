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
    def __init__(self, Actor, sounds, images, clock):
        self.Actor = Actor
        self.sounds = sounds
        self.images = images
        self.clock = clock

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
        
        self.challenger_score = 0
        self.console_score = 0

        # Stuff for the gurk cannon
        cannon = Actor('gurk1')
        cannon.images = ('gurk1','gurk2')
        cannon.center = (constants.WIDTH/2, constants.HEIGHT/2)
        cannon.scale = 0.5
        cannon.spore_timeout = 60
        cannon.fps = 10
        self.cannon = cannon

        self.cannon_in_level = False
        self.cannon_shooting = False
        self.cannon_blast_delay = 500
        self.cannon_blast_timeout = self.cannon_blast_delay
        
        self.ranged_monsters = [cannon]

    def grow_maxine(self):
        self.maxine_current_scale *= MAXINE_CHANGE_FACTOR
        self.maxine.scale = MAXINE_INITIAL_SCALE * self.maxine_current_scale
        
    def shrink_maxine(self):
        self.maxine_current_scale /= MAXINE_CHANGE_FACTOR
        self.maxine.scale = MAXINE_INITIAL_SCALE * self.maxine_current_scale

    def save_arena_to_dict(self):
        save = {}
        wrapper = {'type': 'maxine', 'state': save}

        save['maxine_alive'] = self.maxine.alive
        
        save['maxine'] = self.save_actor_to_dict(self.maxine)
        save['spiraling_monsters'] = [self.save_actor_to_dict(m) for m in self.spiraling_monsters]
        save['dead_monsters'] = [self.save_actor_to_dict(m) for m in self.dead_monsters]
        save['projectiles'] = [self.save_actor_to_dict(m) for m in self.projectiles]
        
        return wrapper

    def save_actor_to_dict(self, actor):
        data = {'pos': list(actor.pos),
                'angle': actor.angle,
                'scale': actor.scale,
                'images': actor.images}
        
        if hasattr(actor, 'disappear_timer'):
            data['disappear_timer'] = actor.disappear_timer
        
        return data

    def load_arena_from_dict(self, wrapper):
        assert(wrapper['type'] == 'maxine')
        save = wrapper['state']
        
        self.maxine = self.load_actor_from_dict(save['maxine'])
        self.maxine.alive = save['maxine_alive']
        
        self.spiraling_monsters = set()
        for data in save['spiraling_monsters']:
            actor = self.load_actor_from_dict(data)
            self.spiraling_monsters.add(actor)

        self.dead_monsters = set()
        for data in save['dead_monsters']:
            actor = self.load_actor_from_dict(data)
            self.dead_monsters.add(actor)

        self.projectiles = set()
        for data in save['projectiles']:
            actor = self.load_actor_from_dict(data)
            self.projectiles.add(actor)
        
    def load_actor_from_dict(self, data):
        images = data['images']
        actor = self.Actor(images[0])
        actor.images = images
        actor.pos = tuple(data['pos'])
        actor.scale = data['scale']
        actor.images = data['images']
        actor.angle = data['angle']

        if 'disappear_timer' in data:
            actor.disappear_timer = data['disappear_timer']

        return actor

    # Maxine methods
    def reward_maxine(self):
        self.sounds.good.play()
        self.challenger_score += 100

    def punish_maxine(self):
        self.sounds.eep.play()
        self.console_score += 100

    def kill_maxine(self):
        '''Used when maxine crashes into an indestructible object such as the pore
        or the gurk cannon, and her position needs to be reset.'''
        self.sounds.eep.play()
        self.maxine.images = self.boom_images()
        self.maxine.fps = 30
        self.maxine.alive = False
        
        delay = 1.0
        self.clock.schedule_unique(self.reset_maxine, delay)
        
        self.console_score += 100

    def reset_maxine(self):
        self.maxine.pos = MAXINE_START
        self.maxine.images = ['maxine']
        self.maxine.alive = True
        
    def boom_images(self):
        return ['boom' + str(i) for i in range(1, 30 + 1)]

