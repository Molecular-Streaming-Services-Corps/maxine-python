import pgzrun
import random
import numpy as np

import data
import util

# Abandoned code to draw a graph using matplotlib. Too slow even for 3 datapoints!
#import matplotlib_pygame

TITLE = 'Maxine\'s Quest'
WIDTH = 1800
HEIGHT = 900

MAXINE_START = (200, 200)

maxine = Actor('maxine')
maxine.pos = MAXINE_START
maxine.sprite_name = 'maxine'
maxine.alive = True

pore = Actor('pore')
pore.center = (WIDTH/2, HEIGHT/2)

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
    
    draw_graph(screen)
    
    pore.draw()

    # Draw Maxine or explosion2
    screen.blit(maxine.sprite_name, (maxine.x, maxine.y))
    
    # Draw either a cell or explosion1
    for cell in cells:
        screen.blit(cell.sprite_name, (cell.x, cell.y))

    for cell in dead_cells:
        screen.blit(cell.sprite_name, (cell.x, cell.y))

    screen.draw.text('SCORE ' + str(score), (10, 10))

def draw_background():
    tile_size = 144

    for x in range(0, WIDTH, tile_size):
        for y in range(0, HEIGHT, tile_size):
            screen.blit('background_living_tissue', (x, y))

i = 0
def draw_graph(screen):
    global i, d
    # Draw a rectangle behind the graph
    RED = (200, 0, 0)
    BLACK = (0, 0, 0)
    GREEN = (0, 200, 0)
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
    elif LIVE:
        raise('Live mode not implemented')
    else:        
        d.get_one_frame_current()
        d.advance_frame()
        y_data = d.boxes
        # In case the min or max value are 0
        min_value = np.min(y_data) - 1
        max_value = np.max(y_data) + 1
        
        
    # Plot the data
    for x, y in enumerate(y_data):
        if y < 0:
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
def update():
    global score, i, step_count, d
    step_count += 1
    if step_count % 10 == 0:
        i += 1
        #print('update(): i:', i)

    if keyboard.q:
        import sys; sys.exit(0)

    # Move Maxine.
    # s is Maxine's speed per frame.
    s = 6
    
    if maxine.alive:
        prev_pos = maxine.pos
    
        if STANDALONE:
            if keyboard.left:
                maxine.left -= s
            elif keyboard.right:
                maxine.left += s
            if keyboard.up:
                maxine.top -= s
            elif keyboard.down:
                maxine.bottom += s
        elif LIVE:
            pass
        else:
            controls = d.get_one_frame_joystick()
            pressed = util.process_joystick_data(controls)
            #print(step_count, controls, pressed)
            if 'js2_left' in pressed:
                maxine.left -= s
            elif 'js2_right' in pressed:
                maxine.left += s
            if 'js2_up' in pressed:
                maxine.top -= s
            elif 'js2_down' in pressed:
                maxine.bottom += s
            
            # Ignore the 2 joystick buttons for now.
        
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

def add_cell():
    cell_type = random.choice(['monster1_right', 'monster2', 'monster3', 'monster4',
        'monster5', 'monster6', 'monster7', 'monster8', 'monster9', 'monster10'])
    cell = Actor(cell_type)
    cell.sprite_name = cell_type
    cell.pos = (pore.x, pore.y)
	# custom parameters
    cell.deltax = random.randrange(-2, 3)
    cell.deltay = random.randrange(-2, 3)
    # Don't let it start with 0 speed
    if cell.deltax == cell.deltay == 0:
        cell.deltax = 1
	
    cells.add(cell)

    delay = random.randrange(5, 8)
    clock.schedule_unique(add_cell, delay)

def kill_cell(cell):
    #print('kill_cell('+cell(str)+')')
    dead_cells.add(cell)
    cell.sprite_name = 'explosion1'
    # Set a disappear timer in frames. Using the clock didn't work for some reason.
    cell.disappear_timer = 15
 
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
LIVE = args.live and not args.datadir
DATADIR = args.datadir

if DATADIR:
    d = data.Data(NUM_BOXES)
    d.load_files(DATADIR)

clock.schedule_unique(add_cell, 4.0)   

music.play('subgenie') 

pgzrun.go()

