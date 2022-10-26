import random
import math
import pygame

import constants

# Grid classes

class Grid:
    '''Abstract base class of grids.'''
    def deadends(self):
        ret = []
        for cell in self.get_cells():
            if len(cell.links) == 1:
                ret.append(cell)
        
        return ret

    def get_rows(self):
        return self.grid
        
    def get_cells(self):
        for row in self.grid:
            for cell in row:
                yield cell
    
    def get_random_cell(self):
        cells = list(self.get_cells())
        return random.choice(cells)
    
    def __str__(self):
        ret = ''
        for row in self.get_rows():
            for cell in row:
                ret += str(cell)
            ret += '\n'
        return ret
    
    def braid(self, p=1.0):
        '''A braid maze is a maze with loops. This function can take a perfect
        maze (i.e. without loops) and knock through a specified proportion of
        the walls to create a braid maze. p is the proportion from 0 to 1.'''
        de = self.deadends()
        random.shuffle(de)
        
        for cell in de:
            if len(cell.get_links()) != 1 or random.random() > p:
                continue
            
            neighbors = [n for n in cell.neighbors() if not cell.is_linked(n)]
            best = [n for n in neighbors if len(n.links) == 1]
            if len(best) == 0:
                best = neighbors
            
            neighbor = random.choice(best)
            cell.link(neighbor)
    
class PolarGrid(Grid):
    def __init__(self, rows):
        '''rows is the number of rows.'''
        self.rows = rows
        self.grid = self.prepare_grid()
        self.configure_cells()
    
    def prepare_grid(self):
        # Uses radians.
        rows = [None for i in range(0, self.rows)]
        
        row_height = 1.0 / self.rows
        rows[0] = [ PolarCell(0, 0) ]
        
        for row in range(1, self.rows):
            radius = row / self.rows
            circumference = 2 * math.pi * radius
            
            previous_count = len(rows[row - 1])
            estimated_cell_width = circumference / previous_count
            ratio = round(estimated_cell_width / row_height)
            
            cells = previous_count * ratio
            rows[row] = [PolarCell(row, col) for col in range(0, cells)]
        
        return rows
        
    def configure_cells(self):
        for cell in self.get_cells():
            row, col = cell.row, cell.column
            
            if row > 0:
                cell.cw = self[row, col + 1]
                cell.ccw = self[row, col - 1]
                
                ratio = len(self.grid[row]) // len(self.grid[row - 1])
                parent = self.grid[row - 1][col // ratio]
                parent.outward.append(cell)
                cell.inward = parent
    
    def __getitem__(self, coords):
        row, column = coords
        if row < 0 or row > self.rows - 1:
            return None
        else:
            num_columns = column % len(self.grid[row])
            return self.grid[row][num_columns]

    def draw(self, screen):
        wall = (0, 0, 0)

        cell_size = constants.TORUS_INNER_RADIUS // self.rows        
        
        for cell in self.get_cells():
            if cell.row == 0:
                continue
                
            # Uses radians.
            theta        = 2 * math.pi / len(self.grid[cell.row])
            inner_radius = cell.row * cell_size
            outer_radius = (cell.row + 1) * cell_size
            theta_ccw    = cell.column * theta
            theta_cw     = (cell.column + 1) * theta
            
            ax = int(inner_radius * math.cos(theta_ccw))
            ay = int(inner_radius * math.sin(theta_ccw))
            bx = int(outer_radius * math.cos(theta_ccw))
            by = int(outer_radius * math.sin(theta_ccw))
            cx = int(inner_radius * math.cos(theta_cw))
            cy = int(inner_radius * math.sin(theta_cw))
            dx = int(outer_radius * math.cos(theta_cw))
            dy = int(outer_radius * math.sin(theta_cw))
            
            ax, ay = self._adjust_coords(ax, ay)
            cx, cy = self._adjust_coords(cx, cy)
            dx, dy = self._adjust_coords(dx, dy)
            
            
            if not cell.is_linked(cell.inward):
                pygame.draw.line(screen.surface, wall, (ax, ay), (cx, cy), width = 3)
            if not cell.is_linked(cell.cw):
                pygame.draw.line(screen.surface, wall, (cx, cy), (dx, dy), width = 3)

        # skip the bounding ellipse because it draws in the wrong place (?!)        
        #bounds = pygame.Rect(
        #    (x - constants.TORUS_INNER_WIDTH // 2, y - constants.TORUS_INNER_HEIGHT // 2),
        #    (x + constants.TORUS_INNER_WIDTH // 2, y + constants.TORUS_INNER_HEIGHT // 2))
        #pygame.draw.ellipse(screen.surface, wall, bounds, width = 3)
        
    def _adjust_coords(self, x, y):
        WIDTH_TO_HEIGHT_RATIO = constants.TORUS_INNER_WIDTH / constants.TORUS_INNER_HEIGHT
        x, y = (WIDTH_TO_HEIGHT_RATIO * x, y)
        x, y = (x + constants.CENTER[0], y + constants.CENTER[1])
        return (x, y)

# Cell classes
    
class Cell:
    '''Abstract base class of cells for any kind of grid. A subclass must
    define neighbors() and attributes for neighbors in specific directions.'''
    def __init__(self, row, column):
        self.row = row
        self.column = column
        self.links = {}
        
    def link(self, cell, bidirectional = True):
        self.links[cell] = True
        if bidirectional:
            cell.link(self, False)
        return self
    
    def unlink(self, cell, bidirectional = True):
        del links[cell]
        if bidirectional:
            cell.unlink(self, False)
        return self
        
    def get_links(self):
        return list(self.links.keys())
        
    def is_linked(self, cell):
        return cell in self.links
        
    def distances(self):
        distances = Distances()
        frontier = [ self ]
        
        while frontier:
            new_frontier = []
            
            for cell in frontier:
                for linked in cell.get_links():
                    if distances[linked]:
                        continue
                    distances[linked] = distances[cell] + 1
                    new_frontier.append(linked)
            frontier = new_frontier
        
        return distances
    
    def __repr__(self):
        return f'{self.__class__.__name__}({self.row}, {self.column})'
     
    def __str__(self):
        return '[ ]'
        
class PolarCell(Cell):
    '''A cell on the polar grid.
    cw stands for the clockwise neighbor, and ccw is counterclockwise.'''
    def __init__(self, row, column):
        super().__init__(row, column)
    
        self.cw = None
        self.ccw = None
        self.inward = None
        self.outward = []
    
    def neighbors(self):
        ret = [n for n in [self.cw, self.ccw, self.inward] if n] + self.outward
        return ret
        
# TODO implement Distances

# Maze generating algorithm classes

class RecursiveBacktracker:
    @staticmethod
    def on(grid, start_at = None):
        if start_at is None:
            start_at = grid.get_random_cell()
            
        stack = []
        stack.append(start_at)
        
        while len(stack) > 0:
            current = stack[-1]
            neighbors = [n for n in current.neighbors() if len(n.get_links()) == 0]
            
            if len(neighbors) == 0:
                stack.pop()
            else:
                neighbor = random.choice(neighbors)
                current.link(neighbor)
                stack.append(neighbor)
                
        return grid

