import random
import logging

# Set up logger for this module
logger = logging.getLogger('components')
logger.setLevel(logging.DEBUG)
import sys
handler = logging.StreamHandler(sys.stdout)
handler.formatter = logging.Formatter('%(asctime)s  %(name)s %(levelname)s: %(message)s')
logger.addHandler(handler)


class BaseComponent:
    pass

# Grid navigation components

class GridNavigation(BaseComponent):
    '''Keeps track of the position of the Actor in the maze.'''
    def __init__(self, grid, in_cell, game):
        self.grid = grid
        self.in_cell = in_cell
        self.game = game

class PolarGridNavigation(GridNavigation):
    '''Adds functions to navigate in a polar grid.'''
    def __init__(self, grid, in_cell, game):
        super().__init__(grid, in_cell, game)
        self.next_cell = None
        self.num_frames_for_move = 60
        self.num_frames_moved = 0
        
    def move_inward(self):
        next_cell =  self.in_cell.inward
        if next_cell and self.in_cell.is_linked(next_cell):
            self.next_cell = next_cell
    
    def move_ccw(self):
        next_cell = self.in_cell.ccw
        if next_cell and self.in_cell.is_linked(next_cell):
            self.next_cell = next_cell

    def move_cw(self):
        next_cell = self.in_cell.cw
        if next_cell and self.in_cell.is_linked(next_cell):
            self.next_cell = next_cell

    def move_outward(self, n):
        '''Moves to the nth outward neighbor. Every cell has at least the 0th outward neighbor
        (except edges). The middle cell has 6 outward neighbors. Some cells have 2 outward neighbors.'''
        outward = self.in_cell.outward
        if len(outward) > n  and self.in_cell.is_linked(outward[n]):
            self.next_cell = outward[n]
    
    def process_keypress(self, keyboard):
        '''Process a keypress by moving. Only relevant to Maxine.
        Uses the buttons 1-6 to move outward.'''
        if not self.finished_moving():
            logging.debug('Pressed a movement key while Maxine was still moving.') 
            return
        
        if keyboard.left:
            self.move_inward()
        elif keyboard.up:
            self.move_ccw()
        elif keyboard.down:
            self.move_cw()
        else:
            numbers_pressed = [keyboard.k_1, keyboard.k_2,
                keyboard.k_3, keyboard.k_4, keyboard.k_5, keyboard.k_6]
            
            for n, pressed in enumerate(numbers_pressed):
                if pressed:
                    self.move_outward(n)
                    break

    def get_location(self):
        if self.next_cell is None:
            return self.grid.get_center(self.in_cell)
        
        # New version
        proportion_moved = self.num_frames_moved / self.num_frames_for_move
        cn = self.grid.get_center(self.next_cell)
        ci = self.grid.get_center(self.in_cell)
        dx_complete = cn[0] - ci[0]
        dy_complete = cn[1] - ci[1]
        
        dx = dx_complete * proportion_moved
        dy = dy_complete * proportion_moved
        
        coords = (ci[0] + dx, ci[1] + dy)
        
        return coords

    def move_to_cell(self, cell):
        self.next_cell = cell
    
    def get_linked_cells(self):
        ret = []
        for c in self.in_cell.neighbors():
            if self.in_cell.is_linked(c):
                ret.append(c)
        return ret

    def finished_moving(self):
        return (self.next_cell is None or self.in_cell == self.next_cell)
    
    def update(self):
        if self.num_frames_moved == self.num_frames_for_move:
            self.in_cell = self.next_cell
            self.next_cell = None
            self.num_frames_moved = 0
        elif self.next_cell is None:
            return
        else:
            # Move the character.
            self.num_frames_moved += 1
            
    
# AI components

class BaseMazeAI(BaseComponent):
    def __init__(self, gridnav):
        self.gridnav = gridnav
        self.game = gridnav.game


class RandomMazeAI(BaseMazeAI):
    '''Takes a random step except it won't reverse its last
    step unless it's in a deadend.'''
    def __init__(self, gridnav):
        super().__init__(gridnav)
        self.prev_cell = gridnav.in_cell
        
    def move(self):
        options = self.gridnav.get_linked_cells()
        # Prefer not to move back to the previous cell.
        best = [c for c in options if c is not self.prev_cell]
        # If we're in a dead end, go to the previous cell after all.
        if not best:
            best = options
        
        if not best:
            return
        else:
            self.prev_cell = self.gridnav.in_cell
            cell = random.choice(best)
            self.gridnav.move_to_cell(cell)
    
    def update(self):
        if self.gridnav.finished_moving():
            self.move()

