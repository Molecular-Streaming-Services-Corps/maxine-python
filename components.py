import random

class BaseComponent:
    pass

# Grid navigation components

class GridNavigation(BaseComponent):
    '''Keeps track of the position of the Actor in the maze.
    Position is a tuple of x and y.'''
    def __init__(self, grid, in_cell):
        self.grid = grid
        self.in_cell = in_cell

class PolarGridNavigation(GridNavigation):
    '''Adds functions to navigate in a polar grid.'''
    def __init__(self, grid, in_cell):
        super().__init__(grid, in_cell)
        
    def move_inward(self):
        next_cell =  self.in_cell.inward
        if next_cell and self.in_cell.is_linked(next_cell):
            self.in_cell = next_cell
    
    def move_ccw(self):
        next_cell = self.in_cell.ccw
        if next_cell and self.in_cell.is_linked(next_cell):
            self.in_cell = next_cell

    def move_cw(self):
        next_cell = self.in_cell.cw
        if next_cell and self.in_cell.is_linked(next_cell):
            self.in_cell = next_cell

    def move_outward(self, n):
        '''Moves to the nth outward neighbor. Every cell has at least the 0th outward neighbor
        (except edges). The middle cell has 6 outward neighbors. Some cells have 2 outward neighbors.'''
        outward = self.in_cell.outward
        if len(outward) > n  and self.in_cell.is_linked(outward[n]):
            self.in_cell = outward[n]
    
    def process_keypress(self, keyboard):
        '''Process a keypress by moving. Only relevant to Maxine.
        Uses the buttons 1-6 to move outward.'''
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
        return self.grid.get_center(self.in_cell)

    def move_to_cell(self, cell):
        self.in_cell = cell
    
    def get_linked_cells(self):
        ret = []
        for c in self.in_cell.neighbors():
            if self.in_cell.is_linked(c):
                ret.append(c)
        return ret

# AI components

class BaseMazeAI(BaseComponent):
    def __init__(self, gridnav):
        self.gridnav = gridnav

class RandomMazeAI(BaseMazeAI):
    def __init__(self, gridnav):
        super().__init__(gridnav)
        
    def move(self):
        options = self.gridnav.get_linked_cells()
        
        if not options:
            return
        else:
            cell = random.choice(options)
            self.gridnav.move_to_cell(cell)

