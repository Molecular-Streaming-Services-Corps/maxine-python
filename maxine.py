#!/bin/env python3
# Installed packages.
import pgzrun
from pgzhelper import *
import pygame
import numpy as np
import cv2

# Builtin packages.
import random
import threading

# Local packages.
import data
import util
import lilith_client
import animated_image
import serialization

# Abandoned code to draw a graph using matplotlib. Too slow even for 3 datapoints!
#import matplotlib_pygame

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

class Controls:
    '''The obsolete controls'''
    def __init__(self):
        self.bias = 0.0
    
        # Setup onscreen controls
        self.arrow_size = 64
        start_x = 10 + self.arrow_size
        start_y = 300
        
        horizontal_gap = 200
        vertical_offset = self.arrow_size * 2
        raise_x = start_x + self.arrow_size + horizontal_gap
    
        self.bias_lower = Actor('arrow_red_left')
        self.bias_lower.pos = (start_x, start_y)
        self.bias_raise = Actor('arrow_red_right')
        self.bias_raise.pos = (raise_x, start_y)
        
        self.syringe_lower = Actor('arrow_red_left')
        self.syringe_lower.pos = (start_x, start_y + vertical_offset * 1)
        self.syringe_raise = Actor('arrow_red_right')
        self.syringe_raise.pos = (raise_x, start_y + vertical_offset * 1)
        
        # We're not going to change the sample rate for now.
        #self.sample_rate_lower = Actor('arrow_red_left')
        #self.sample_rate_lower.pos = (start_x, start_y + vertical_offset * 2)
        #self.sample_rate_raise = Actor('arrow_red_right')
        #self.sample_rate_raise.pos = (raise_x, start_y + vertical_offset * 2)

        self.control_actors = [self.bias_lower, self.bias_raise,
            self.syringe_lower, self.syringe_raise]
        #    self.sample_rate_lower, self.sample_rate_raise]

    def draw(self):
        for arrow in self.control_actors:
            arrow.draw()

        # Draw the text.
        blx, bly = self.bias_lower.left, self.bias_lower.top
        coords = (blx + self.arrow_size, bly)
        text = f'BIAS: {self.bias}mV'
        screen.draw.text(text, coords)

        sx, sy = self.syringe_lower.left, self.syringe_lower.top
        coords = (sx + self.arrow_size, sy)
        text = 'SYRINGE'
        screen.draw.text(text, coords)

        #srx, sry = self.sample_rate_lower.left, self.sample_rate_lower.top
        #coords = (srx + self.arrow_size, sry)
        #text = 'SAMPLE RATE: 100kHz'
        #screen.draw.text(text, coords)

    def check(self):
        '''Only call this when space or joystick button is pressed'''
        for i, actor in enumerate(self.control_actors):
            if maxine.colliderect(actor):
                print(f'Maxine pressed button #{i}')

        if maxine.colliderect(self.bias_lower):
            self.bias -= 1000
            if LIVE:
                lilith_client.set_bias(self.bias)
        elif maxine.colliderect(self.bias_raise):
            self.bias += 1000
            if LIVE:
                lilith_client.set_bias(self.bias)

class NewControls:
    def __init__(self):
        # LCD font
        pygame.font.init()
        self.font = pygame.font.Font('ds-digi.ttf', 40)
        
        self.voltage_knob = Actor('voltage_knob')
        self.voltage_knob.left = 10
        self.voltage_knob.top = 10

        self.bg = Actor('led_display')
        self.bg.left = 10
        # voltage_knob.png is 83x83 and the voltage knob is drawn at 10,10
        self.bg.top = 10 + 83 + 10

        self.zap_lever = Actor('switch_big_frame_1')
        self.zap_lever.images = ['switch_big_frame_1']
        self.zap_lever.left = 10
        self.zap_lever.top = self.bg.bottom + 10
        
        self.zap_timeout = 0
        
        self.controls = [self.voltage_knob, self.zap_lever]
        # The index of the presently selected control
        self.control_index = 0
        self.voltage_index = 0
        self.zap_index = 1
        
        self.old_voltage = 0
        self.voltage = 0
        
    def update(self):
        if self.zap_timeout > 0:
            self.zap_timeout -= 1
            self.zap_lever.images = ['switch_big_frame_2']
        else:
            self.zap_lever.images = ['switch_big_frame_1']
            
            self.set_voltage(self.old_voltage)
            self.voltage_knob.angle = 360 - self.old_voltage
        
        self.zap_lever.animate()

        # Hack: continuously rotate the voltage knob to test the display
        #self.voltage_knob.angle = int((self.voltage_knob.angle - 1) % 360)
        
    def draw_text(self, text, coords):
        RED = (255, 0, 0)
        surface = self.font.render(text, False, RED)
        screen.blit(surface, coords)

    def draw(self):
        # Set the control that's presently selected to be a bit bigger.
        for control in self.controls:
            control.scale = 1
        self.controls[self.control_index].scale = 1.2
     
        self.voltage_knob.draw()
        
        self.bg.draw()
        
        self.draw_text(str(self.voltage) + ' MV', (self.bg.left + 15, self.bg.top + 2))

        self.zap_lever.draw()

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
        
    def push_left(self):
        if self.control_index == self.voltage_index:
            self.voltage_knob.angle = int((self.voltage_knob.angle + 36) % 360)
            voltage = 360 - self.voltage_knob.angle
            self.set_voltage(voltage)
            self.old_voltage = voltage
        
    def push_right(self):
        if self.control_index == self.voltage_index:
            self.voltage_knob.angle = int((self.voltage_knob.angle - 36) % 360)
            voltage = 360 - self.voltage_knob.angle
            self.set_voltage(voltage)
            self.old_voltage = voltage

    def set_voltage(self, voltage):
        if LIVE:
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
        
        return wrapper
        
    def load_from_dict(self, wrapper):
        assert(wrapper['type'] == 'controls')
        save = wrapper['state']
        
        self.control_index = save['control_index']
        self.voltage_knob.angle = save['voltage_knob_angle']
        self.voltage = save['voltage']
        self.old_voltage = save['old_voltage']
        self.zap_timeout = save['zap_timeout']

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

def draw():
    global rotation
    # Murky green background color
    #screen.fill((128, 128, 0))
    
    # For now we're drawing a video background (this can be included later)
    draw_living_background()
    #draw_video()
    #draw_metal_background()
    
    # Abandoned code to draw a graph using matplotlib. Too slow even for 3 datapoints!
    #matplotlib_pygame.draw_graph(screen)
    
    draw_graph()
    
    if PLAYER == 'console':
        new_controls.draw()
    
    # In the old 1-player mode Maxine needed to touch controls on screen.
    #controls.draw()
    
    if PLAYER == 'maxine':
        # Replaced by Kent's video of a pore
        #pore.draw()

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
    #screen.draw.circle((WIDTH/2, HEIGHT/2), RING_RADIUS, RED)
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
        # Draw the victory or gameover graphics.
        if maxine_current_scale <= MAXINE_LOSE_SIZE:
            gameover = Actor('gameover')
            gameover.pos = CENTER
            gameover.draw()
        elif maxine_current_scale >= MAXINE_WIN_SIZE:
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
    tile_size = 144

    for x in range(0, WIDTH, tile_size):
        for y in range(0, HEIGHT, tile_size):
            screen.blit('background_living_tissue', (x, y))

def draw_metal_background():
    surface = getattr(images, 'bg_cut')
    surface = pygame.transform.scale(surface, (WIDTH, HEIGHT))
    screen.blit(surface, (0, 0))

video = None
restart_video = True
def draw_video():
    global video, restart_video

    if restart_video:
        video = cv2.VideoCapture("backgroundpore.mp4")
        restart_video = False

    success, video_image = video.read()
    if success:
        video_surf = pygame.image.frombuffer(
            video_image.tobytes(), video_image.shape[1::-1], "BGR")
        video_surf = pygame.transform.scale(video_surf, (WIDTH, HEIGHT))
        screen.blit(video_surf, (0, 0))
    else:
        restart_video = True    

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
    global score, i, step_count, d, controls, space_pressed_before, button_pressed_before
    global maxine_current_scale
    step_count += 1
    if step_count % 10 == 0:
        i += 1
        #print('update(): i:', i)

    if keyboard.q:
        import sys; sys.exit(0)
    
    # Advance the datafile and make a monster appear on a spike.
    # If we're in STANDALONE mode, a timer will make the monster appear.
    if DATADIR:
        d.get_one_frame_current()
        d.advance_frame()
        
        if PLAYER == 'maxine' and d.middle_spike_exists():
            add_cell()
    elif LIVE:
        d.load_received_samples()
        if PLAYER == 'maxine' and d.middle_spike_exists():
            add_cell()    

    if PLAYER == 'maxine':
        update_for_maxine_player()
    else:
        update_for_console_player()

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
            
        if keyboard.space:
            if not space_pressed_before:
                space_pressed_before = True
                controls.check()
        else:
            space_pressed_before = False

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

def point_outside_signal_ring(point):
    '''Calculate if a position is outside the ellipse. From Math StackExchange.'''
    rx = RING_WIDTH / 2
    ry = RING_HEIGHT / 2
    scaled_coords = (point[0] - CENTER[0],
                     (point[1] - CENTER[1]) * rx/ry)
    return np.linalg.norm(scaled_coords, 2) > rx

def on_key_down(key):
    global graph_type, new_controls, serializer

    # Change graph type
    if key == keys.G:
        if graph_type == 'heatmap':
            graph_type = 'scatterplot'
        else:
            graph_type = 'heatmap'
    
    # Save and load the state of the game to a file.
    if key == keys.S:
        if PLAYER == 'console':
            data = new_controls.save_to_dict()
            serializer.save_dict_to_file(data, 'console.json')
    elif key == key.L:
        if PLAYER == 'console':
            data = serializer.load_dict_from_file('console.json')
            new_controls.load_from_dict(data)

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

if not args.player:
    PLAYER = 'maxine'
else:
    PLAYER = args.player # 'console'

if DATADIR:
    d = data.PrerecordedData(NUM_BOXES)
    d.load_files(DATADIR)

elif STANDALONE:
    if PLAYER == 'maxine':
        clock.schedule_unique(add_cell, 4.0)   

elif LIVE:
    lilith_client.MAC = lilith_client.NAME2MAC[args.live]
    lilith_client.setup()

    # Run the Lilith interaction loop in another thread
    t = threading.Thread(target=lilith_client.main)
    # Don't wait for this thread when the game exits
    t.setDaemon(True)
    t.start()
    
    d = data.LiveData(NUM_BOXES)


controls = Controls()

serializer = serialization.Serializer()

#music.play('subgenie') 

pgzrun.go()

import sys; sys.exit(0)
