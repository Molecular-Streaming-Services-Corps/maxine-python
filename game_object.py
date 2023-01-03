import math

import constants

MAXINE_START = (constants.CENTER[0] + 200, constants.CENTER[1]) #(200, 600)

# Certain levels might use scaling in the future.
MAXINE_INITIAL_SCALE = 0.5
MAXINE_CHANGE_FACTOR = 1.2
'''These will make Maxine win when she is 4x the size (after about 8 hits) or
lose when she is a quarter of the size.'''
MAXINE_WIN_SIZE = 4
MAXINE_LOSE_SIZE = 0.25

# Singleton
game = None

class Game:
    def __init__(self, Actor, sounds, images, clock):
        self.Actor = Actor
        self.sounds = sounds
        self.images = images
        self.clock = clock

        self.maxine_current_scale = 1
        
        maxine = Actor('maxine_neutral')
        maxine.images = ['maxine_neutral']
        maxine.pos = MAXINE_START
        maxine.alive = True
        maxine.scale = MAXINE_INITIAL_SCALE * self.maxine_current_scale
        self.maxine = maxine
        
        self.pore = Actor('pore')
        self.pore.center = (constants.WIDTH/2, constants.HEIGHT/2)

        self.spiraling_monsters = set()
        self.bouncing_monsters = set()
        self.walking_monsters = set()
        self.dead_monsters = set()
        self.maze_monsters = set()
        self.items = set()
        
        self.projectiles = set()
        
        # Only to be used in the simulated Battle Royale mode
        self.other_maxines = []
        
        self.challenger_score = 0
        self.console_score = 0

        # Stuff for the mushroom cannon
        cannon = Actor('mushromancer1')
        cannon.images = ('mushromancer1','mushromancer2', 'mushromancer3',
            'mushromancer4')
        cannon.center = (constants.WIDTH/2, constants.HEIGHT/2)
        cannon.scale = 1
        cannon.spore_timeout = 60
        cannon.fps = 10
        self.cannon = cannon
        
        self.cannon_in_level = False
        self.cannon_shooting = False
        self.cannon_blast_delay = 500
        self.cannon_blast_timeout = self.cannon_blast_delay
        
        self.ranged_monsters = [cannon]
        
        # This is required for the level with a dancing shroom and rotating spores to work
        self.draw_spirals = True
        
        self.question_text = 'What size are these fungal spores? Do we have a large enough pore?'
        self.shown_question_length = 34
        self.shown_question_start = 0
        self.frames_per_character = 2

        self.step_count = 0
        
        self.rms_last_second = None

        # These are changed in the Battle Royale level
        self.draw_panels = True
        
        # Size of the play ring
        self.torus_outer_height = 900
        self.torus_outer_width = 1280

        self.torus_inner_height = self.torus_outer_height - constants.TORUS_THICKNESS  * 2
        self.torus_inner_width = self.torus_outer_width - constants.TORUS_THICKNESS * 2
        self.torus_inner_radius = min(self.torus_inner_height, self.torus_inner_width) // 2

        self.ring_height = self.torus_outer_height - 66
        self.ring_width = self.torus_outer_width - 66
        self.ring_radius = min(self.ring_height, self.ring_width) // 2


    def make_other_maxines(self):
        '''Make all of the 8 other Maxines.'''
        for i in range(0, 8):
            maxine = self.Actor('maxine_neutral')
            maxine.images = ['maxine_neutral']
            maxine.pos = MAXINE_START
            maxine.alive = True
            maxine.scale = MAXINE_INITIAL_SCALE
            self.other_maxines.append(maxine)
       
        return self.other_maxines

    def draw(self, screen):
        #screen.draw.text(self.get_question_section(), center = (255, 835), fontname = "ds-digi.ttf", fontsize = 20, color = "red")
        screen.draw.text(self.get_question_section(), (100, 825), fontname = "ds-digi.ttf", fontsize = 20, color = "red")

    def draw_title_screen(self, screen):
        screen.draw.text('Press space to begin.', center = (900, 450),
            fontname = "ds-digi.ttf", fontsize = 60, color = "red")

    def update(self):
        self.step_count += 1
        if self.step_count % self.frames_per_character == 0:
            self.shown_question_start += 1
            if self.shown_question_start >= len(self.question_text):
                self.shown_question_start = 0

    def get_question_section(self):
        ret = self.question_text[self.shown_question_start : self.shown_question_start + self.shown_question_length]
        return ret

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
        self.maxine.images = ['maxine_neutral']
        self.maxine.alive = True
    
    def boom_images(self):
        return ['boom' + str(i) for i in range(1, 30 + 1)]

    def hit_maze_monster(self, monster):
        if monster is self.maxine:
            return

        hit = self.maxine.fighter.give_hit()
        monster.fighter.take_hit(hit)
        
        if monster.fighter.is_dead():
            self.kill_maze_monster(monster)
        else:
            self.sounds.good.play()

    def kill_maze_monster(self, monster):
        if monster is self.maxine:
            return
    
        self.maze_monsters.remove(monster)
        self.dead_monsters.add(monster)
        monster.images = self.boom_images()
        monster.fps = 30
        monster.scale = 0.25
        
        # Set a disappear timer in frames.
        monster.disappear_timer = 31
        
        self.reward_maxine()

    def cannon_dance(self):
        if self.rms_last_second is None or math.isnan(self.rms_last_second):
            self.cannon.fps = 1
            return
        
        rms_range = constants.MAX_RMS - constants.MIN_RMS
        if self.rms_last_second > constants.MAX_RMS:
            rms = constants.MAX_RMS
        elif self.rms_last_second < constants.MIN_RMS:
            rms = constants.MIN_RMS
        else:
            rms = self.rms_last_second

        ratio = (rms - constants.MIN_RMS) / rms_range
        # It's more fun if his minimum speed is 1 fps instead of 0 fps
        self.cannon.fps = int(10 * ratio) + 1

