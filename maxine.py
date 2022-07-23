import pgzrun
import random
import numpy as np

# Abandoned code to draw a graph using matplotlib. Too slow even for 3 datapoints!
#import matplotlib_pygame

TITLE = 'Maxine\'s Quest'
WIDTH = 1800
HEIGHT = 900

MAXINE_START = (100, 56)

maxine = Actor('maxine')
maxine.pos = MAXINE_START
maxine.sprite_name = 'maxine'
maxine.alive = True

pore = Actor('pore')
pore.center = (WIDTH/2, HEIGHT/2)

cells = set()
dead_cells = set()

score = 0

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
    global i
    # Draw a rectangle behind the graph
    RED = (200, 0, 0)
    BLACK = (0, 0, 0)
    GREEN = (0, 200, 0)
    BOX = Rect((9, 99), (302, 82))
    screen.draw.filled_rect(BOX, GREEN)
    
    num_boxes = 100
    
    # Sample data for the graph
    x_data = list(range(0, num_boxes))
    x_data = [(x + i) % num_boxes for x in x_data]
    inputs = [2*np.pi*x/num_boxes for x in x_data]
    y_data = np.sin(inputs)  # update the data.
    #print('i', i)
    #print('x_data:', x_data)
    #print('inputs:', inputs)
    #print('y_data:', y_data)
    
    # Calculate the color and location of each rectangle and draw it
    MIN_VALUE = -1.0
    MAX_VALUE = +1.0
    for x, y in enumerate(y_data):
        if y < 0:
            scale_factor = y / MIN_VALUE
            # Shades of red
            color = (255 * scale_factor, 0, 0)
        else:
            scale_factor = y / MAX_VALUE
            # Shades of blue
            color = (0, 0, 255 * scale_factor)
        
        rect = Rect((10 + 300.0 / num_boxes * x , 100), (300 / num_boxes, 80))
        
        screen.draw.filled_rect(rect, color)

step_count = 0
def update():
    global score, i, step_count
    step_count += 1
    if step_count % 10 == 0:
        i += 1
        #print('update(): i:', i)

    if keyboard.q:
        import sys; sys.exit(0)

    # Move Maxine.
    if maxine.alive:
        if keyboard.left:
            maxine.left -= 6
        elif keyboard.right:
            maxine.left += 6
        if keyboard.up:
            maxine.top -= 6
        elif keyboard.down:
            maxine.bottom += 6
        
        # Detect if Maxine gets too close to the pore. (She'll explode!)
        dist = maxine.distance_to(pore.center)
        if dist < 100:
            kill_maxine()
    
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
STANDALONE = args['datadir'] == None and not args['live']
LIVE = args['live'] and not args['datadir']
DATADIR = args['datadir']

clock.schedule_unique(add_cell, 4.0)   

music.play('subgenie') 

pgzrun.go()

