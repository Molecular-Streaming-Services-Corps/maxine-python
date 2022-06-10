import pgzrun
import random

maxine = Actor('maxine')
maxine.pos = (100, 56)

pore = Actor('pore')
pore.pos = (450, 350)

cells = set()

score = 0

TITLE = 'Maxine\'s Molecular Adventure'
WIDTH = 900
HEIGHT = 700

def draw():
    screen.fill((128, 128, 0))
    maxine.draw()
    pore.draw()
    for cell in cells:
    	cell.draw()
    screen.draw.text('SCORE ' + str(score), (10, 10))

def update():
    global score

    # Move Maxine.
    if keyboard.left:
        maxine.left -= 2
    elif keyboard.right:
        maxine.left += 2
    if keyboard.up:
        maxine.top -= 2
    elif keyboard.down:
        maxine.bottom += 2
    
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

        
def on_mouse_down(pos, button):
    if button == mouse.LEFT and maxine.collidepoint(pos):
        sounds.eep.play()
        print("Eek!")

def add_cell():
    cell_type = random.choice(['cell1', 'cell2'])
    cell = Actor(cell_type)
    cell.pos = (450, 350)
	# custom parameters
    cell.deltax = random.randrange(-2, 3)
    cell.deltay = random.randrange(-2, 3)
	
    cells.add(cell)

    clock.schedule_unique(add_cell, 10)

clock.schedule_unique(add_cell, 4.0)   

music.play('subgenie') 

pgzrun.go()

