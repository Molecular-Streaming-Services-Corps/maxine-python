#!/usr/bin/env python
# Installed packages.
import pgzrun
from pgzhelper import *
import pygame
import numpy as np
# For the video
import cv2
import logging
import time

# Builtin packages.
import random
import threading

# Local packages.
import data
import util
import lilith_client
import animated_image
import serialization
import image_ops
import music_ops
import spike_graph

# Set up logger for this module
logger = logging.getLogger('maxine')
logger.setLevel(logging.DEBUG)
import sys
handler = logging.StreamHandler(sys.stdout)
handler.formatter = logging.Formatter('%(asctime)s  %(name)s %(levelname)s: %(message)s')
logger.addHandler(handler)

TITLE = 'Maxine\'s µMonsters'
WIDTH = 1800
HEIGHT = 900
CENTER = (WIDTH / 2, HEIGHT / 2)
RING_RADIUS = 350
RING_HEIGHT = 700
RING_WIDTH = 1000

MAXINE_START = (CENTER[0] + 100, CENTER[1]) #(200, 600)
'''If this is set to False, Maxine explodes instead of changing size when she
is hurt, and just gets points when she kills a monster.'''
MAXINE_CHANGES_SIZE = True
MAXINE_INITIAL_SCALE = 0.25
MAXINE_CHANGE_FACTOR = 1.2
'''These will make Maxine win when she is 4x the size (after about 8 hits) or
lose when she is a quarter of the size.'''
MAXINE_WIN_SIZE = 4
MAXINE_LOSE_SIZE = 0.25
maxine_current_scale = 1

maxine = Actor('maxine')
maxine.images = ['maxine']
maxine.pos = MAXINE_START
maxine.alive = True
maxine.scale = MAXINE_INITIAL_SCALE * maxine_current_scale

pore = Actor('pore')
pore.center = (WIDTH/2, HEIGHT/2)

animations = set()

#graph_type = 'heatmap'
graph_type = 'ring'

MAKE_MUSHROOMS = True
DRAW_SPIRALS = False

game_state = 'playing' # becomes 'won' or 'lost'
playing_music = True

sg = None

# Temporary development tool
dev_control = None

class NewControls:
    def __init__(self):
        # Pink panel in the bottom right
        self.panel = Actor('panel')
        self.panel.right = WIDTH
        self.panel.bottom = HEIGHT
    
        # LCD font
        pygame.font.init()
        self.font = pygame.font.Font('ds-digi.ttf', 40)
        
        self.voltage_knob = Actor('voltage_knob')
        #self.voltage_knob.left = 10
        #self.voltage_knob.top = 10
        self.voltage_knob.pos = (1596, 527)

        #self.bg = Actor('led_display')
        #self.bg.left = 10
        ## voltage_knob.png is 83x83 and the voltage knob is drawn at 10,10
        #self.bg.top = 10 + 83 + 10

        self.zap_lever = Actor('switch_big_frame_1')
        self.zap_lever.images = ['switch_big_frame_1']
        #self.zap_lever.left = 10
        #self.zap_lever.top = 10
        self.zap_lever.pos = (1730, 579)
        
        self.zap_timeout = 0
        
        self.syringe = Actor('syringe')
        #self.syringe.left = 1470
        #self.syringe.top = 545
        self.syringe.pos = (1477, 399)
        
        # This is an index into a list of speed settings. Can be negative.
        self.pump_speed_index = 0
        self.pump_speed_delays = [20, 10, 5, 2, 1]
        
        self.hydrowag_switch = Actor('switch_green_off')
        self.hydrowag_switch.images = ['switch_green_off']
        self.hydrowag_switch.pos = (1731, 665)
        self.hydrowag_on = False
        self.hydrowag_moving_forward = True
        self.hydrowag_timeout = 0
        
        self.sawtooth_switch = Actor('switch_blue_off')
        self.sawtooth_switch.images = ['switch_blue_off']
        self.sawtooth_switch.pos = (1731, 719)
        self.sawtooth_on = False
        self.sawtooth_frame = 0

        self.potion_holder = PotionHolder()

        self.drop_button = Actor('button_off')
        self.drop_button.images = ['button_off']
        self.drop_button.pos = (1483, 707)
        self.button_timeout = 0
        
        self.controls = [self.voltage_knob, self.zap_lever, self.syringe,
                         self.hydrowag_switch, self.sawtooth_switch,
                         self.potion_holder, self.drop_button]
        # The index of the presently selected control
        self.control_index = 0
        self.voltage_index = 0
        self.zap_index = 1
        self.syringe_index = 2
        self.hydrowag_index = 3
        self.sawtooth_index = 4
        self.potion_index = 5
        self.drop_index = 6
        
        self.old_voltage = 0
        self.voltage = 0
        self.old_angle = 0
          
    def update(self):
        # Zapper stuff
        if PLAYER == 'console':
            if self.zap_timeout > 0:
                self.zap_timeout -= 1    

        # This code runs on both maxine and console, so maxine can draw the lever correctly
        # when the timeout is updated over the internet
        if self.zap_timeout > 0:
            self.zap_lever.images = ['switch_big_frame_2']
        else:
            self.zap_lever.images = ['switch_big_frame_1']
            
            if self.voltage != self.old_voltage:
                self.set_voltage(self.old_voltage)
            self.voltage_knob.angle = self.old_angle
        
        self.zap_lever.animate()

        # Hydrowag stuff
        if self.hydrowag_on:
            self.hydrowag_switch.images = ['switch_green_on']
        else:
            self.hydrowag_switch.images = ['switch_green_off']
        
        self.hydrowag_switch.animate()
        
        # Move the pump back and forward fast
        if self.hydrowag_on and PLAYER == 'console' and LIVE:
            if self.hydrowag_timeout > 0:
                self.hydrowag_timeout -= 1
                
                if self.hydrowag_moving_forward:
                    lilith_client.move_pump(500, 1)
                else:
                    lilith_client.move_pump(-500, 1)
            else:
                self.hydrowag_moving_forward = not self.hydrowag_moving_forward
                self.hydrowag_timeout = 60

        # Sawtooth stuff
        if self.sawtooth_on:
            self.sawtooth_switch.images = ['switch_blue_on']
        else:
            self.sawtooth_switch.images = ['switch_blue_off']
        
        self.sawtooth_switch.animate()

        if self.sawtooth_on and PLAYER == 'console' and LIVE:
            if self.sawtooth_frame == 60:
                self.sawtooth_frame = 0
            else:
                self.sawtooth_frame += 1
            
            MIN_VOLTAGE = -1000
            MAX_VOLTAGE = 3500
            RANGE = MAX_VOLTAGE - MIN_VOLTAGE
            voltage = int(RANGE * self.sawtooth_frame / 60 + MIN_VOLTAGE)
            self.set_voltage(voltage)

            # Only change the angle while sawtooth is on
            v = self.find_angle_from_voltage(self.voltage)
            if v:
                self.voltage_knob.angle = v

        # Hack: continuously rotate the voltage knob to test the display
        #self.voltage_knob.angle = int((self.voltage_knob.angle - 1) % 360)
        
        # Move the pump if required (controlled by the syringe)
        if LIVE and PLAYER == 'console' and LIVE:
            #logger.debug('pump_speed_index: %s', self.pump_speed_index)
            if self.pump_speed_index == 0:
                # Override the current number of steps and stop the pump
                lilith_client.move_pump(0, 0)
            elif self.pump_speed_index > 0:
                idx = self.pump_speed_index - 1
                lilith_client.move_pump(500, self.pump_speed_delays[idx])
            else:
                idx = abs(self.pump_speed_index) - 1
                lilith_client.move_pump(-500, self.pump_speed_delays[idx])
        
        self.potion_holder.update()

        # Stuff for the drop-adding button        
        if self.button_timeout == 0:
            self.drop_button.images = ['button_off']
        else:
            self.drop_button.images = ['button_on']
            self.button_timeout -= 1

        self.drop_button.animate()

    def draw_text(self, text, coords):
        RED = (255, 0, 0)
        surface = self.font.render(text, False, RED)
        screen.blit(surface, coords)

    def draw(self):
        self.panel.draw()
    
        # Set the control that's presently selected to be a bit bigger.
        for control in self.controls:
            control.scale = 1
        self.controls[self.control_index].scale = 1.2
        self.drop_button.scale *= 0.5
     
        self.voltage_knob.draw()
        
        #self.bg.draw()
        
        #self.draw_text(str(self.voltage) + ' MV', (self.bg.left + 15, self.bg.top + 2))
        self.draw_text(str(self.voltage) + ' MV', (1545, 594))

        self.zap_lever.draw()
        
        self.syringe.draw()
        
        self.hydrowag_switch.draw()
        
        self.sawtooth_switch.draw()

        self.potion_holder.draw()
        
        self.drop_button.draw()
        
        # Draw the number of drops added
        ph = self.potion_holder
        drops = ph.get_drops()
        self.draw_text(str(drops), (1470, 770))

    def select_down(self):
        '''Select the control below the present one. Wraps around.'''
        self.control_index = (self.control_index + 1) % len(self.controls)

    def select_up(self):
        '''Select the control above the present one. Wraps around.'''
        self.control_index = (self.control_index - 1) % len(self.controls)

    def push(self):
        if self.control_index == self.zap_index:
            # 100 milliseconds in frames
            self.zap_timeout = 6
            
            # Send a message to change the voltage
            self.set_voltage(3500)
        elif self.control_index == self.hydrowag_index:
            self.hydrowag_on = not self.hydrowag_on
            # hydrowag has just been turned on now
            if self.hydrowag_on:
                self.hydrowag_moving_forward = True
                self.hydrowag_timeout = 60
        elif self.control_index == self.sawtooth_index:
            self.sawtooth_on = not self.sawtooth_on
            if self.sawtooth_on:
                self.old_voltage = self.voltage
                self.old_angle = self.voltage_knob.angle
            else:
                self.set_voltage(self.old_voltage)
                self.voltage_knob.angle = self.old_angle
        elif self.control_index == self.drop_index:
            # Only respond when the button is up
            if self.button_timeout == 0:
                self.potion_holder.on_button_pushed()
        
            self.button_timeout = 6
        
    def push_left(self):
        if self.control_index == self.voltage_index:
            if self.voltage_knob.angle != 170: # +17 * 10
                self.voltage_knob.angle = (self.voltage_knob.angle + 17) % 360

            voltage = self.find_voltage_from_angle(self.voltage_knob.angle)
            self.set_voltage(voltage)
            self.old_voltage = voltage
            self.old_angle = self.voltage_knob.angle
        elif self.control_index == self.syringe_index:
            self.pump_speed_index = min(len(self.pump_speed_delays), 
                                        self.pump_speed_index + 1)
        elif self.control_index == self.potion_index:
            self.potion_holder.push_left()
        
    def push_right(self):
        if self.control_index == self.voltage_index:
            if self.voltage_knob.angle != 190: # -17 * 10
                self.voltage_knob.angle = (self.voltage_knob.angle - 17) % 360
            
            voltage = self.find_voltage_from_angle(self.voltage_knob.angle)
            self.set_voltage(voltage)
            self.old_voltage = voltage
            self.old_angle = self.voltage_knob.angle
        elif self.control_index == self.syringe_index:
            self.pump_speed_index = max(-len(self.pump_speed_delays), 
                                        self.pump_speed_index - 1)
        elif self.control_index == self.potion_index:
            self.potion_holder.push_right()

    def find_voltage_from_angle(self, angle):
        if angle in [360, 0]:
            voltage = 0
        elif angle > 0 and angle <= 170:
            # Negative voltage
            voltage = int(-1 * angle / 17 * 100)
        else:
            # Positive voltage
            angle_compliment = (360 - angle) % 360
            voltage = int(angle_compliment / 17 * 100)

        return voltage

    def find_angle_from_voltage(self, voltage):
        if voltage > 1000 or voltage < -1000:
            angle = 190
        elif voltage == 0:
            angle = 0
        elif voltage > 0:
            angle = int(360 - voltage / 100 * 17)
        else:
            # Negative voltage
            angle = int(-voltage / 100 * 17)
        
        return angle

    def set_voltage(self, voltage):
        if LIVE and PLAYER == 'console':
            lilith_client.set_bias(voltage)
        self.voltage = voltage

    def save_to_dict(self):
        save = {}
        wrapper = {'type': 'controls', 'state': save}
        
        save['control_index'] = self.control_index
        save['voltage_knob_angle'] = self.voltage_knob.angle
        save['voltage'] = self.voltage
        save['old_voltage'] = self.old_voltage
        save['zap_timeout'] = self.zap_timeout
        save['hydrowag_on'] = self.hydrowag_on
        save['sawtooth_on'] = self.sawtooth_on
        
        ph = self.potion_holder
        save['potion_selected'] = ph.selected
        save['drops_readout'] = ph.get_drops()
        
        save['button_timeout'] = self.button_timeout
        
        return wrapper
        
    def load_from_dict(self, wrapper):
        assert(wrapper['type'] == 'controls')
        save = wrapper['state']
        
        self.control_index = save['control_index']
        self.voltage_knob.angle = save['voltage_knob_angle']
        self.voltage = save['voltage']
        self.old_voltage = save['old_voltage']
        
        # Let the update function move the control except when the lever is first pressed
        zt = save['zap_timeout']
        if zt == 6:
            self.zap_timeout = zt
        
        self.hydrowag_on = save['hydrowag_on']
        self.sawtooth_on = save['sawtooth_on']
        self.potion_holder.selected = save['potion_selected']
        self.potion_holder.num_drops[self.potion_holder.selected] = save['drops_readout']
        
        bt = save['button_timeout']
        if bt == 6:
            self.button_timeout = bt

class PotionHolder:
    def __init__(self):
        self.holder = Actor('potion_holder')
        self.holder.pos = (1600, 730)
    
        self.selected = 0
        self.potions = [None] * 4
        self.actors = [Actor(f'potion_{n}') for n in range(1, 4 + 1)] 
        self.scale = 1
    
        self.num_drops = [0, 0, 0, 0]
        # This list contains (list not tuple) pairs of
        # [timestamp, potion index] for when a potion was dropped
        self.drop_history = []

    def update(self):
        self.set_indexes()
        
    def set_indexes(self):
        self.potions[(0 - self.selected) % 4] = self.actors[0]
        self.potions[(1 - self.selected) % 4] = self.actors[1]
        self.potions[(2 - self.selected) % 4] = self.actors[2]
        self.potions[(3 - self.selected) % 4] = self.actors[3]
        
        self.holder.scale = self.scale
        # Draw the top potion bigger
        for i in range(0, 4):
            self.potions[i].scale = 0.5 * self.scale
        self.potions[0].scale = 0.7 * self.scale
        
        # Move them all to the correct position
        self.potions[0].pos = (1602, 680)
        self.potions[1].pos = (1654, 726)
        self.potions[2].pos = (1611, 788)
        self.potions[3].pos = (1556, 739)
    
    def draw(self):
        self.holder.draw()
        
        for potion in self.potions:
            potion.draw()

    def push_left(self):
        self.selected = (self.selected + 1) % 4

    def push_right(self):
        self.selected = (self.selected - 1) % 4

    def on_button_pushed(self):
        global serializer
    
        self.num_drops[self.selected] += 1
        
        update = [time.time(), self.selected]
        self.drop_history.append(update)

        if LIVE:
            data = self.num_drops
            json_string = serializer.save_dict_to_string(data)
            lilith_client.set_metadata('drop_counts', json_string)
            
            data = self.drop_history
            json_string =  serializer.save_dict_to_string(data)
            lilith_client.set_metadata('drop_history', json_string)
    
            # Check if it worked
            lilith_client.get_metadata('drop_counts', lilith_client.ws)
            lilith_client.get_metadata('drop_history', lilith_client.ws)
            
    def get_drops(self):
        return self.num_drops[self.selected]

new_controls = NewControls()

cells = set()
dead_cells = set()

spiraling_monsters = set()
dead_sms = set()

projectiles = set()

score = 0

# Represents data from a stored file.
d = None

NUM_BOXES = 100

rotation = 0

def save_arena_to_dict():
    save = {}
    wrapper = {'type': 'maxine', 'state': save}

    save['maxine_alive'] = maxine.alive
    
    save['maxine'] = save_actor_to_dict(maxine)
    save['spiraling_monsters'] = [save_actor_to_dict(m) for m in spiraling_monsters]
    save['dead_sms'] = [save_actor_to_dict(m) for m in dead_sms]
    save['projectiles'] = [save_actor_to_dict(m) for m in projectiles]
    
    return wrapper

def save_actor_to_dict(actor):
    data = {'pos': list(actor.pos),
            'angle': actor.angle,
            'scale': actor.scale,
            'images': actor.images}
    
    if hasattr(actor, 'disappear_timer'):
        data['disappear_timer'] = actor.disappear_timer
    
    return data

def load_arena_from_dict(wrapper):
    global maxine, spiraling_monsters, dead_sms, projectiles

    assert(wrapper['type'] == 'maxine')
    save = wrapper['state']
    
    maxine = load_actor_from_dict(save['maxine'])
    maxine.alive = save['maxine_alive']
    
    spiraling_monsters = set()
    for data in save['spiraling_monsters']:
        actor = load_actor_from_dict(data)
        spiraling_monsters.add(actor)

    dead_sms = set()
    for data in save['dead_sms']:
        actor = load_actor_from_dict(data)
        dead_sms.add(actor)

    projectiles = set()
    for data in save['projectiles']:
        actor = load_actor_from_dict(data)
        projectiles.add(actor)
    
def load_actor_from_dict(data):
    images = data['images']
    actor = Actor(images[0])
    actor.images = images
    actor.pos = tuple(data['pos'])
    actor.scale = data['scale']
    actor.images = data['images']
    actor.angle = data['angle']

    if 'disappear_timer' in data:
        actor.disappear_timer = data['disappear_timer']

    return actor

def draw():
    global rotation, dev_control, sg
    draw_living_background()

    # Draw the microscope video in front of the background and behind the signal ring
    draw_video()
    
    draw_graph()
    
    if sg:
        sg.draw()
    
    # Now we draw the controls for both players.
    new_controls.draw()
    
    if dev_control:
        dev_control.draw()

    # Draw Maxine or the boom
    maxine.draw()
    
    # Draw either a cell or explosion1
    for cell in cells:
        draw_cell(cell)

    for cell in dead_cells:
        draw_cell(cell)

    for monster in spiraling_monsters:
        monster.draw()
    for monster in dead_sms:
        monster.draw()
        
    for p in projectiles:
        p.draw()

    if not MAXINE_CHANGES_SIZE:
        screen.draw.text('SCORE ' + str(score), (10, 10))
    
    # Draw the signal ring.
    RED = (200, 0, 0)
    ring_rect = Rect((CENTER[0] - RING_WIDTH / 2, CENTER[1] - RING_HEIGHT / 2), 
                     (RING_WIDTH, RING_HEIGHT))
    pygame.draw.ellipse(screen.surface, RED, ring_rect, width = 1)
    
    if DRAW_SPIRALS:
        # Draw spirals to indicate where the monsters will move
        WHITE = (255, 255, 255)
        BLUE = (0, 0, 255)
        GREEN = (0, 200, 0)
        rotation += 1
        draw_spiral(rotation + 0, WHITE)
        draw_spiral(rotation + 180, GREEN)

    if PLAYER == 'maxine':
        # Draw the victory or gameover graphics (or nothing if the game is still going).
        if game_state == 'lost':
            gameover = Actor('gameover')
            gameover.pos = CENTER
            gameover.draw()
        elif game_state == 'won':
            victory = Actor('victory')
            victory.pos = CENTER
            victory.draw()

def draw_cell(cell):
    if hasattr(cell, 'animation'):
        surface = getattr(images, cell.animation.get_current_image_name())
        surface = pygame.transform.scale(surface, (200, 200))
        screen.blit(surface, (cell.x, cell.y))
    else:
        screen.blit(cell.sprite_name, (cell.x, cell.y))    

def draw_living_background():
    global step_count
    
    tile_size = 144
    
    offset = step_count % tile_size

    for x in range(-tile_size, WIDTH, tile_size):
        for y in range(-tile_size, HEIGHT, tile_size):
            screen.blit('background_living_tissue', (x + offset, y + offset))

def draw_metal_background():
    surface = getattr(images, 'bg_cut')
    surface = pygame.transform.scale(surface, (WIDTH, HEIGHT))
    screen.blit(surface, (0, 0))

# Code for displaying the microscope footage inside the signal ring
video = None
restart_video = True
frame = 0
surf = None
video_image = None
def update_video():
    global frame, video, restart_video, video_image, surf, sg
    frame += 1

    if not sg:
        sg = spike_graph.SpikeGraph(screen, Rect)

    if restart_video:
        video = cv2.VideoCapture('cats.mp4')
        restart_video = False

    # Get one frame as an OpenCV image
    prev_image = video_image
    if frame % 2 in [0]:
        success, video_image = video.read()
    else:
        success = True
    if success:
        if video_image is None:
            return
            
        # Change it to our format
        img = np.array(video_image)
        img = img.transpose([1, 0, 2])
        img = img[:,:,::-1]

        light_purple = 203, 195, 227
        bright_purple = 191, 64, 191
        image_ops.tint(img, light_purple)
        display = image_ops.composite(image_ops.ellipse, image_ops.green_image, img)
        
        # Get pygame surface (it's created from an array with no alpha channel
        # so it has no alpha channel itself).
        surf = pygame.surfarray.make_surface(display)
        surf.set_colorkey((0, 255, 0))
        surf = pygame.transform.scale(surf, (RING_WIDTH, RING_HEIGHT))
    else:
        restart_video = True    
        frame = 0

def draw_video():
    global surf
    
    if surf:
        x = (WIDTH - RING_WIDTH) // 2
        y = (HEIGHT - RING_HEIGHT) // 2
        screen.blit(surf, (x, y))

i = 0
def draw_graph():
    global i, d
    # Draw a rectangle behind the graph
    RED = (200, 0, 0)
    BLACK = (0, 0, 0)
    GREEN = (0, 200, 0)
    WHITE = (255, 255, 255)
    BLUE = (0, 0, 255)
    if graph_type != 'ring':
        BOX = Rect((9, 99), (302, 82))
        screen.draw.filled_rect(BOX, GREEN)
    
    NEON_PINK = (251,72,196) # Positive
    GRAPE = (128,49,167) # Negative
    
    # Sample data for the graph
    if STANDALONE:
        x_data = list(range(0, NUM_BOXES))
        x_data = [(x + i) % NUM_BOXES for x in x_data]
        inputs = [2*np.pi*x/NUM_BOXES for x in x_data]
        y_data = np.sin(inputs)  # update the data.
        abs_y_data = y_data
        #print('i', i)
        #print('x_data:', x_data)
        #print('inputs:', inputs)
        #print('y_data:', y_data)
    
        # Calculate the color and location of each rectangle and draw it
        min_value = -1.0
        max_value = +1.0
    else: # live or prerecorded mode        
        y_data = d.get_scaled_boxes()
        abs_y_data = d.get_absolute_scaled_boxes()
        min_value = -1.0
        max_value = +1.0
    
    MIDPOINT = NUM_BOXES // 2
    
    # Plot the data
    for x, (y, abs_y) in enumerate(zip(y_data, abs_y_data)):
        if x == MIDPOINT:
            # A single white line
            color = WHITE
            abs_y = 0
        elif x == 0:
            # A black line at the origin
            color = RED
            abs_y = 0
        elif y < 0:
            scale_factor = y / min_value
            # Shades of red
            #color = (255 * scale_factor, 0, 0)
            color = np.multiply(scale_factor, BLUE)
        else:
            scale_factor = y / max_value
            # Shades of blue
            #color = (0, 0, 255 * scale_factor)
            color = np.multiply(scale_factor, NEON_PINK)
            
        if graph_type == 'heatmap':
            rect = Rect((10 + 300.0 / NUM_BOXES * x , 100), (300 / NUM_BOXES, 80))
            screen.draw.filled_rect(rect, color)
        elif graph_type == 'scatterplot':
            # Draw a 3x1 Rect because there's no function to draw a pixel
            # y coord is between 100 and 180
            y_coord = int(140 + 40 * -y)
            rect = Rect((10 + 300.0 / NUM_BOXES * x, y_coord), (3, 1))
            screen.draw.filled_rect(rect, color)        
        else:
            pass
            # Draw lines around an ellipse using polar coordinates
            LINE_LENGTH = 50
            
            # Calculate the offset, used to display absolute values.
            offset = abs_y * LINE_LENGTH / 2
            
            # Calculate the coordinates for the inner end of the line
            r = RING_RADIUS - LINE_LENGTH / 2 + offset
            theta = x / NUM_BOXES * 360
            (inner_x, inner_y) = util.pol2cart(r, theta)
            inner_coords = adjust_coords(inner_x, inner_y)
            
            # Calculate the coordinates for the outer end of the line
            r = RING_RADIUS + LINE_LENGTH / 2 + offset
            (outer_x, outer_y) = util.pol2cart(r, theta)
            outer_coords = adjust_coords(outer_x, outer_y)
            
            # Finally draw the line
            pygame.draw.line(screen.surface, color, inner_coords, outer_coords, width = 10)

def adjust_coords(x, y):
    # Stretch in the x dimension to match the greater width of the ellipse,
    # and then add the center to the Cartesian coordinates
    WIDTH_TO_HEIGHT_RATIO = RING_WIDTH / RING_HEIGHT

    (x, y) = (WIDTH_TO_HEIGHT_RATIO * x, y)
    (x, y) = (x + CENTER[0], y + CENTER[1])
    return (x, y)

def draw_spiral(rotation, color):
    GAP = 0.5
    MAX_THETA = 690
    STEP_DEGREES = 10
    
    for theta in range(0, MAX_THETA, STEP_DEGREES):
        (x, y) = util.spiral(GAP, rotation, theta)
        (x, y) = adjust_coords(x, y)
        screen.draw.filled_circle((x, y), 1, color)

def boom_images():
    return ['boom' + str(i) for i in range(1, 30 + 1)]

step_count = 0
space_pressed_before = False
button_pressed_before = False
def update():
    global score, i, step_count, d, space_pressed_before, button_pressed_before
    global maxine_current_scale
    global new_controls
    global logger
    global playing_music
    global sg
    step_count += 1
    if step_count % 10 == 0:
        i += 1
        #print('update(): i:', i)

    if keyboard.q:
        import sys; sys.exit(0)
    
    # Update the microscope video
    update_video()
    
    # Advance the datafile and make a monster appear on a spike.
    # If we're in STANDALONE mode, a timer will make the monster appear.
    if DATADIR:
        d.get_one_frame_current()
        
        data = d.get_frame()
        if playing_music:
            music_ops.current_to_frequency(data)
            music_ops.current_to_volume(data)
        
        spike_exists = d.middle_spike_exists()
        if spike_exists:
            sg.set_frame(data)
        
        d.advance_frame()
        
        if PLAYER == 'maxine' and spike_exists:
            add_cell()
    elif LIVE:
        spikes = d.load_received_samples_and_count_spikes()
    
        data = d.get_frame()
        if playing_music:
            music_ops.current_to_frequency(data)    
            music_ops.current_to_volume(data)
        
        # todo set it to the last frame containing a spike
        sg.set_frame(data)
    
        if PLAYER == 'maxine':
            for i in range(0, spikes):
                add_cell()    

    if PLAYER == 'maxine':
        if game_state == 'playing':
            update_for_maxine_player()
        
            # Send updates to the other player    
            if MULTIPLAYER:
                wrapper = save_arena_to_dict()
                json_string = serializer.save_dict_to_string(wrapper)
                lilith_client.send_status(json_string)
    else:
        update_for_console_player()

        if MULTIPLAYER:
            wrapper = new_controls.save_to_dict()
            json_string = serializer.save_dict_to_string(wrapper)
            lilith_client.send_status(json_string)

    # Process updates only from the other player.
    state_d_list = lilith_client.consume_latest_samples(lilith_client.state_q)
    for state_data in state_d_list:
        wrapper = serializer.load_dict_from_string(state_data.json_string)
        ty = wrapper['type']
        if ty == 'controls' and PLAYER == 'maxine':
            new_controls.load_from_dict(wrapper)
            logger.info('loaded controls state from the internet')
        elif ty == 'maxine' and PLAYER == 'console':
            load_arena_from_dict(wrapper)
            logger.info('loaded arena state from the internet')

pressed_before = set()
def update_for_console_player():
    '''Allows the console player to use either the joystick or the keyboard
    (for testing) to manipulate the onscreen controls.'''
    global pressed_before, new_controls

    new_controls.update()

    # Determine the list of pressed joystick switches
    if LIVE:
        pressed = d.pressed
    elif DATADIR:
        joystick_binary = d.get_one_frame_joystick()
        pressed = util.process_joystick_data(joystick_binary)
        #print(step_count, joystick_binary, pressed)
    else:
        # In standalone mode, we say no joystick buttons are pressed.
        pressed = []

    # Equivalent joystick and keyboard controls.
    on = {}
    on['left'] = 'js1_left' in pressed or keyboard.left
    on['right'] = 'js1_right' in pressed or keyboard.right
    on['up'] = 'js1_up' in pressed or keyboard.up
    on['down'] = 'js1_down' in pressed or keyboard.down
    on['button'] = 'js1_b1' in pressed or keyboard.space

    # See if each switch went down in this frame.
    # This allows you to make controls that only respond one time for each time the switch
    # is pressed.
    pressed_just_now = set()
    for switch_name in on.keys():
        check_pressed_just_now(switch_name, on, pressed_before, pressed_just_now)

    # Finally respond to the switches/keys that have been turned on this frame.
    if 'up' in pressed_just_now:
        new_controls.select_up()
    elif 'down' in pressed_just_now:
        new_controls.select_down()
    
    # Some controls only respond the moment the button is pressed.
    if 'button' in pressed_just_now:
        new_controls.push()

    # In contrast, allow the player to press and hold the button while pressing
    # left and right.
    if on['button']:        
        if 'left' in pressed_just_now:
            new_controls.push_left()
        elif 'right' in pressed_just_now:
            new_controls.push_right()

def check_pressed_just_now(switch_name, on, pressed_before, pressed_just_now):
    if on[switch_name]:
        if not switch_name in pressed_before:
            pressed_before.add(switch_name)
            pressed_just_now.add(switch_name)
    else:
        if switch_name in pressed_before:
            pressed_before.remove(switch_name)
    
def update_for_maxine_player():
    global maxine_current_scale, game_state, new_controls
    # This will update the images used on the controls. It won't send any duplicate signals to the server.
    new_controls.update()

    maxine.animate()

    # Move Maxine.
    # s is Maxine's speed per frame.
    s = 6
    
    if maxine.alive:
        prev_pos = maxine.pos

        # Allow the user to use either the keyboard or the joystick    
        if keyboard.left:
            maxine.left -= s
        elif keyboard.right:
            maxine.left += s
        if keyboard.up:
            maxine.top -= s
        elif keyboard.down:
            maxine.bottom += s
            
        # The old controls.
        #if keyboard.space:
        #    if not space_pressed_before:
        #        space_pressed_before = True
        #        controls.check()
        #else:
        #    space_pressed_before = False

        if LIVE:
            pressed = d.pressed
        elif DATADIR:
            joystick_binary = d.get_one_frame_joystick()
            pressed = util.process_joystick_data(joystick_binary)
            #print(step_count, joystick_binary, pressed)
        else:
            # In standalone mode, we say no joystick buttons are pressed.
            pressed = []
                            
        JOYSTICK_MOVES_MAXINE = False
        if JOYSTICK_MOVES_MAXINE:
            if 'js1_left' in pressed:
                maxine.left -= s
            elif 'js1_right' in pressed:
                maxine.left += s
            if 'js1_up' in pressed:
                maxine.top -= s
            elif 'js1_down' in pressed:
                maxine.bottom += s
            
            if 'js1_b1' in pressed:
                if not button_pressed_before:
                    button_pressed_before = True
                    controls.check()
            else:
                button_pressed_before = False
        
        # Now we have collide_pixel
        # Detect if Maxine gets too close to the pore. (She'll explode!)
        #dist = maxine.distance_to(pore)
        #if dist < 100:
        #    kill_maxine()
        if maxine.collide_pixel(pore):
            kill_maxine()
        
        # This is not used now there is a signal ring.
        # Stop Maxine at the edges of the screen.
        #if maxine.left < 0 or maxine.right > WIDTH or maxine.top < 0 or maxine.bottom > HEIGHT:
        #    maxine.pos = prev_pos
        
        # Obsolete code for a circular signal ring
        #dist = util.distance_points(maxine.center, CENTER)
        #if dist > RING_RADIUS:
        #    maxine.pos = prev_pos
        
        if point_outside_signal_ring(maxine.center):
            maxine.pos = prev_pos
    
    # Can't remove items from a set during iteration.
    to_remove = []
    # Let Maxine eat cells.
    for cell in cells:
        if maxine.colliderect(cell):
            sounds.eep.play()
            score += 100
            to_remove.append(cell)
    
    for cell in to_remove:
        cells.remove(cell)
        kill_cell(cell)
    
    # Make dead cells disappear after a certain amount of time.
    to_remove = []
    for cell in dead_cells:
        cell.disappear_timer -= 1
        
        if cell.disappear_timer <= 0:
            to_remove.append(cell)
            
    for cell in to_remove:
        remove_dead_cell(cell)
    
    #if maxine.left > WIDTH:
    #    maxine.right = 0

    # Move cells.
    for cell in cells:
        cell.left += cell.deltax
        cell.top += cell.deltay
        if cell.left > WIDTH:
            cell.deltax *= -1
        if cell.top > HEIGHT:
            cell.deltay *= -1
        if cell.right < 0:
            cell.deltax *= -1
        if cell.bottom < 0:
            cell.deltay *= -1

    # Update animations (obsoleted by PGZHelper)
    for animation in animations:
        animation.update()

    # Process spiraling monsters
    sm_to_blow_up = set()
    for monster in spiraling_monsters:
        monster.animate()
        
        # Move along the spiral
        ss = monster.spiral_state
        ss.update()
        monster.pos = ss.pos
        monster.angle = (ss.angle + 90) % 360
        
        # Blow up the monster when it gets to the center for now
        if util.distance_points(monster.center, CENTER) < 20:
            sm_to_blow_up.add(monster)

        # Blow up monsters that collide with Maxine
        if maxine.collide_pixel(monster):
            sm_to_blow_up.add(monster)
            
            if MAXINE_CHANGES_SIZE:
                maxine_current_scale *= MAXINE_CHANGE_FACTOR
                maxine.scale = MAXINE_INITIAL_SCALE * maxine_current_scale
            
        # Spawn a spore if we are far enough from Maxine and time is up
        monster.spore_timeout -= 1
        if monster.spore_timeout <= 0 and monster.distance_to(maxine) > 300:
            monster.spore_timeout = get_spore_timeout()
            make_spore(monster)

    for monster in sm_to_blow_up:
        spiraling_monsters.remove(monster)
        dead_sms.add(monster)
        monster.images = boom_images()
        monster.fps = 30
        monster.scale = 0.25
        
        # Set a disappear timer in frames.
        monster.disappear_timer = 31
        
    to_delete = set()
    for monster in dead_sms:
        monster.animate()
        monster.disappear_timer -= 1

        if monster.disappear_timer <= 0:
            to_delete.add(monster)
            
    for monster in to_delete:
        dead_sms.remove(monster)

    # Handle projectiles (spores in the case of mushrooms)
    # Projectiles point toward Maxine when they're spawned. (Spored?)
    SPORE_SPEED = 3
    projectiles_to_delete = set()
    for p in projectiles:
        p.animate()
        p.move_forward(SPORE_SPEED)
        if maxine.collide_pixel(p):
            projectiles_to_delete.add(p)
            
            if MAXINE_CHANGES_SIZE:
                maxine_current_scale /= MAXINE_CHANGE_FACTOR
                maxine.scale = MAXINE_INITIAL_SCALE * maxine_current_scale
            else:
                kill_maxine()
        # For a circular ring.
        #elif util.distance_points(p.center, CENTER) > RING_RADIUS:
        elif point_outside_signal_ring(p.center):
            # Delete projectiles that hit the ring
            projectiles_to_delete.add(p)
    
    for p in projectiles_to_delete:
        projectiles.remove(p)

    # Check if Maxine has won or lost (or is still going)
    if maxine_current_scale <= MAXINE_LOSE_SIZE:
        game_state = 'lost'
    elif maxine_current_scale >= MAXINE_WIN_SIZE:
        game_state = 'won'

def point_outside_signal_ring(point):
    '''Calculate if a position is outside the ellipse. From Math StackExchange.'''
    rx = RING_WIDTH / 2
    ry = RING_HEIGHT / 2
    scaled_coords = (point[0] - CENTER[0],
                     (point[1] - CENTER[1]) * rx/ry)
    return np.linalg.norm(scaled_coords, 2) > rx

def on_key_down(key):
    global graph_type, new_controls, serializer, playing_music

    # Change graph type
    if key == keys.G:
        if graph_type == 'heatmap':
            graph_type = 'scatterplot'
        else:
            graph_type = 'heatmap'
    
    # Turn music on and off
    if key == keys.M:
        playing_music = not playing_music
    
    # Save and load the state of the game to a file.
    if key == keys.S:
        # Only save the information that this player is in charge of updating
        if PLAYER == 'console':
            data = new_controls.save_to_dict()
            serializer.save_dict_to_file(data, 'console.json')
        else:
            data = save_arena_to_dict()
            serializer.save_dict_to_file(data, 'maxine.json')
    elif key == key.L:
        # Load the Maxine information only for the console player, because
        # the save information isn't complete enough to continue the game,
        # just enough to display one frame. But the console information is
        # enough to continue operating the console.
        if PLAYER == 'maxine':
            data = serializer.load_dict_from_file('console.json')
            new_controls.load_from_dict(data)

        if PLAYER == 'console':
            data = serializer.load_dict_from_file('maxine.json')
            load_arena_from_dict(data)

# Development tool: when the mouse is clicked, print the mouse coordinates in the window
def on_mouse_down(pos):
    print('Mouse clicked at:', pos)

# Temporary development tool: move a control around on the screen
def on_mouse_move(pos):
    global dev_control
    #dev_control = Actor('button_off')
    #dev_control.pos = pos
    #dev_control.scale = 0.5
    pass

# Maxine functions

def kill_maxine():
    sounds.eep.play()
    maxine.images = boom_images()
    maxine.fps = 30
    maxine.alive = False
    
    delay = 1.0
    clock.schedule_unique(reset_maxine, delay)

def reset_maxine():
    maxine.pos = MAXINE_START
    maxine.images = ['maxine']
    maxine.alive = True

# Cell/Monster functions
def make_spore(shroom):
    '''Makes a spore starting at the center of the shroom and heading toward
    Maxine.'''
    spore = Actor('spore')
    spore.images = ['spore1', 'spore2', 'spore3']
    spore.scale = 0.25
    spore.pos = shroom.pos
    spore.point_towards(maxine)
    projectiles.add(spore)
    return spore

def get_spore_timeout():
    return random.randrange(60 * 2.5, 60 * 5)

def make_mushroom():
    mush = Actor('mushdance1')
    mush.images = ['mushdance1', 'mushdance2', 'mushdance3']
    mush.fps = 3
    mush.scale = 0.5
    
    # Set up the spiraling behavior with a component
    rotation = random.randrange(0, 360)
    mush.spiral_state = util.SpiralState(
        0.5, rotation, 690, 1, CENTER, RING_WIDTH / RING_HEIGHT)
    
    # Set the mushroom up to spawn a spore
    mush.spore_timeout = get_spore_timeout()
    
    return mush

def make_midjourney_monster():
    cell_type = random.choice(['monster1_right', 'monster2', 'monster3', 'monster4',
        'monster5', 'monster6', 'monster7', 'monster8', 'monster9', 'monster10'])
    cell = Actor(cell_type)
    cell.sprite_name = cell_type
    return cell

def make_sars_monster():
    global animations

    cell_types = [('corn', 3), ('gurk', 2), ('icar', 3), ('lem', 19), ('olive', 4), ('sna', 3)]
    name, num_frames = random.choice(cell_types)
    animation = animated_image.AnimatedImage(name, num_frames)
    animations.add(animation)
    
    cell = Actor(name + '1')
    cell.animation = animation
    return cell

def add_cell():
    # This is called by the clock, not the update function (in standalone mode)
    global game_state
    if game_state != 'playing':
        return
        
    if MAKE_MUSHROOMS:
        mush = make_mushroom()
        spiraling_monsters.add(mush)
    else:
        cell = make_sars_monster()

        cell.pos = (pore.x, pore.y)
	    # custom parameters
        cell.deltax = random.randrange(-2, 3)
        cell.deltay = random.randrange(-2, 3)
        # Don't let it start with 0 speed
        if cell.deltax == cell.deltay == 0:
            cell.deltax = 1
	    
        cells.add(cell)

    if STANDALONE:
        delay = random.randrange(5, 8)
        clock.schedule_unique(add_cell, delay)

def kill_cell(cell):
    global animations
    
    #print('kill_cell('+cell(str)+')')
    if hasattr(cell, 'animation'):
        animations.remove(cell.animation)
        
    dead_cells.add(cell)
    # Old approach for MidJourney graphics
    #cell.sprite_name = 'explosion1'
    boom_animation = animated_image.AnimatedImage('boom', 30)
    cell.animation = boom_animation
    animations.add(boom_animation)
    # Set a disappear timer in frames. Using the clock didn't work for some reason.
    cell.disappear_timer = 31
 
    # Don't know why this good code doesn't work. remove_dead_cell never gets called.
    
#    def remove_this_dead_cell():
#        remove_dead_cell(cell)
#        
#    clock.schedule_unique(remove_this_dead_cell, 0.5)

def remove_dead_cell(cell):
    #print('remove_dead_cell('+str(cell)+')')
    dead_cells.remove(cell)

import parse_arguments
args = parse_arguments.parser.parse_args()
STANDALONE = not args.datadir and not args.live
LIVE = args.live
DATADIR = args.datadir
MULTIPLAYER = not args.player is None

if not args.player:
    PLAYER = 'maxine'
else:
    PLAYER = args.player # 'console'

BOARD = args.live # Could be None

# Detect Kent's computer and apply default parameters (can be overridden)
import platform
import sys
if platform.system() == 'Darwin' and len(sys.argv) == 1:
    BOARD = 'Kent'
    LIVE = True
    PLAYER = 'console'
    STANDALONE = False
    DATADIR = None

TITLE = TITLE + f' ({PLAYER})'

if DATADIR:
    d = data.PrerecordedData(NUM_BOXES)
    d.load_files(DATADIR)

elif STANDALONE:
    if PLAYER == 'maxine':
        clock.schedule_unique(add_cell, 4.0)   

elif LIVE:
    lilith_client.MAC = lilith_client.NAME2MAC[BOARD]
    lilith_client.setup()

    # Run the Lilith interaction loop in another thread
    t = threading.Thread(target=lilith_client.main)
    # Don't wait for this thread when the game exits
    t.setDaemon(True)
    t.start()
    
    d = data.LiveData(NUM_BOXES)

if MULTIPLAYER and not LIVE:
    name = 'Kent'
    lilith_client.MAC = lilith_client.NAME2MAC[name]
    lilith_client.setup()

    print('Initializing lilith_client')
    # Run the Lilith interaction loop in another thread
    t = threading.Thread(target=lilith_client.main)
    # Don't wait for this thread when the game exits
    t.setDaemon(True)
    t.start()

serializer = serialization.Serializer()

#music.play('subgenie') 

pgzrun.go()

import sys; sys.exit(0)
