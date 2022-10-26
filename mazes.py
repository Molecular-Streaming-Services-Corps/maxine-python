import random
import math

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
        cells = list(self.get_cells)
        return random.choice(cells)
    
    def __str__(self):
        ret = ''
        for row in self.get_rows():
            for cell in row:
                ret += str(cell)
            ret += '\n'
        return ret
    
    # TODO implement braid
    
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
        ret = [n for n in [self.cw, self.ccw, self.inward] if n] + outward
        
# TODO implement Distances

