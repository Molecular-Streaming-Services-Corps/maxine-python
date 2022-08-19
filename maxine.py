#!/bin/env python3
# Installed packages.
import pgzrun
import pygame.transform
import numpy as np

# Builtin packages.
import random
import threading

# Local packages.
import data
import util
import lilith_client
import animated_image

# Abandoned code to draw a graph using matplotlib. Too slow even for 3 datapoints!
#import matplotlib_pygame

TITLE = 'Maxine\'s Quest'
WIDTH = 1800
HEIGHT = 900

MAXINE_START = (200, 600)

maxine = Actor('maxine')
maxine.pos = MAXINE_START
maxine.sprite_name = 'maxine'
maxine.alive = True

pore = Actor('pore')
pore.center = (WIDTH/2, HEIGHT/2)

animations = set()

class Controls:
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

cells = set()
dead_cells = set()

score = 0

# Represents data from a stored file.
d = None

NUM_BOXES = 100

def draw():
    # Murky green background color
    #screen.fill((128, 128, 0))
    draw_background()
    
    # Abandoned code to draw a graph using matplotlib. Too slow even for 3 datapoints!
    #matplotlib_pygame.draw_graph(screen)
    
    draw_graph()
    
    controls.draw()
        
    pore.draw()

    # Draw Maxine or explosion2
    screen.blit(maxine.sprite_name, (maxine.x, maxine.y))
    
    # Draw either a cell or explosion1
    for cell in cells:
        draw_cell(cell)

    for cell in dead_cells:
        draw_cell(cell)

    screen.draw.text('SCORE ' + str(score), (10, 10))

def draw_cell(cell):
    if hasattr(cell, 'animation'):
        surface = getattr(images, cell.animation.get_current_image_name())
        surface = pygame.transform.scale(surface, (200, 200))
        screen.blit(surface, (cell.x, cell.y))
    else:
        screen.blit(cell.sprite_name, (cell.x, cell.y))    

def draw_background():
    tile_size = 144

    for x in range(0, WIDTH, tile_size):
        for y in range(0, HEIGHT, tile_size):
            screen.blit('background_living_tissue', (x, y))

i = 0
def draw_graph():
    global i, d
    # Draw a rectangle behind the graph
    RED = (200, 0, 0)
    BLACK = (0, 0, 0)
    GREEN = (0, 200, 0)
    WHITE = (255, 255, 255)
    BOX = Rect((9, 99), (302, 82))
    screen.draw.filled_rect(BOX, GREEN)
    
    # Sample data for the graph
    if STANDALONE:
        x_data = list(range(0, NUM_BOXES))
        x_data = [(x + i) % NUM_BOXES for x in x_data]
        inputs = [2*np.pi*x/NUM_BOXES for x in x_data]
        y_data = np.sin(inputs)  # update the data.
        #print('i', i)
        #print('x_data:', x_data)
        #print('inputs:', inputs)
        #print('y_data:', y_data)
    
        # Calculate the color and location of each rectangle and draw it
        min_value = -1.0
        max_value = +1.0
    else: # live or prerecorded mode        
        y_data = d.get_scaled_boxes()
        min_value = -1.0
        max_value = +1.0
    
    MIDPOINT = NUM_BOXES // 2
    
    # Plot the data
    for x, y in enumerate(y_data):
        if x == MIDPOINT:
            # A single white line
            color = WHITE
        elif y < 0:
            scale_factor = y / min_value
            # Shades of red
            color = (255 * scale_factor, 0, 0)
        else:
            scale_factor = y / max_value
            # Shades of blue
            color = (0, 0, 255 * scale_factor)
        
        rect = Rect((10 + 300.0 / NUM_BOXES * x , 100), (300 / NUM_BOXES, 80))
        
        screen.draw.filled_rect(rect, color)

step_count = 0
space_pressed_before = False
button_pressed_before = False
def update():
    global score, i, step_count, d, controls, space_pressed_before, button_pressed_before
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
        
        if d.middle_spike_exists():
            add_cell()
    elif LIVE:
        d.load_received_samples()
        if d.middle_spike_exists():
            add_cell()    

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
        
        # Detect if Maxine gets too close to the pore. (She'll explode!)
        dist = maxine.distance_to(pore.center)
        if dist < 100:
            kill_maxine()
        
        # Stop Maxine at the edges of the screen.
        if maxine.left < 0 or maxine.right > WIDTH or maxine.top < 0 or maxine.bottom > HEIGHT:
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

    # Update animations
    for animation in animations:
        animation.update()

# Maxine functions

def kill_maxine():
    sounds.eep.play()
    maxine.sprite_name = 'explosion2'
    maxine.alive = False
    
    delay = 1.0
    clock.schedule_unique(reset_maxine, delay)

def reset_maxine():
    maxine.pos = MAXINE_START
    maxine.sprite_name = 'maxine'
    maxine.alive = True

# Cell functions

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

if DATADIR:
    d = data.PrerecordedData(NUM_BOXES)
    d.load_files(DATADIR)

elif STANDALONE:
    clock.schedule_unique(add_cell, 4.0)   

elif LIVE:
    lilith_client.MAC = lilith_client.NAME2MAC[args.live]
    lilith_client.setup()

    # Run the Lilith interaction loop in another thread
    t = threading.Thread(target=lilith_client.main)
    t.start()
    
    d = data.LiveData(NUM_BOXES)


controls = Controls()

#music.play('subgenie') 

pgzrun.go()

import sys; sys.exit(0)
