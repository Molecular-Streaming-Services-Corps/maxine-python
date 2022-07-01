import pgzrun
import random

TITLE = 'Maxine\'s Quest'
WIDTH = 1800
HEIGHT = 900

MAXINE_START = (100, 56)

maxine = Actor('maxine')
maxine.pos = MAXINE_START
maxine_sprite_name = 'maxine'

pore = Actor('pore')
pore.pos = (WIDTH/2, HEIGHT/2)

cells = set()
dead_cells = set()

score = 0

def draw():
    screen.fill((128, 128, 0))
    maxine.draw()
    pore.draw()
    
    # Draw either a cell or the explosion
    for cell in cells:
        screen.blit(cell.sprite_name, (cell.x, cell.y))

    for cell in dead_cells:
        screen.blit(cell.sprite_name, (cell.x, cell.y))

    screen.draw.text('SCORE ' + str(score), (10, 10))

def update():
    global score

    # Move Maxine.
    if keyboard.left:
        maxine.left -= 6
    elif keyboard.right:
        maxine.left += 6
    if keyboard.up:
        maxine.top -= 6
    elif keyboard.down:
        maxine.bottom += 6
    
    # Detect if Maxine gets too close to the pore. (She'll fall in or get zapped or something)
    dist = maxine.distance_to((pore.x, pore.y))
    if dist < 100:
        maxine.left, maxine.top = MAXINE_START
    
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

    clock.schedule_unique(add_cell, 7.0)

def kill_cell(cell):
    #print('kill_cell('+cell(str)+')')
    dead_cells.add(cell)
    cell.sprite_name = 'explosion1'
    # Set a disappear timer in frames.
    cell.disappear_timer = 15
 
    # Don't know why this good code doesn't work. remove_dead_cell never gets called.
    
#    def remove_this_dead_cell():
#        remove_dead_cell(cell)
#        
#    clock.schedule_unique(remove_this_dead_cell, 0.5)

def remove_dead_cell(cell):
    #print('remove_dead_cell('+str(cell)+')')
    dead_cells.remove(cell)

clock.schedule_unique(add_cell, 4.0)   

music.play('subgenie') 

pgzrun.go()

