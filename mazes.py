import random
import math
import pygame

import constants
import util
import colors

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
        the deadends to create a braid maze. p is the proportion from 0 to 1.'''
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
    
    def remove_walls(self, p=0.2):
        '''Randomly remove a certain percentage of the walls.
        Returns a list of the walls removed as tuples of (cell1, cell2).'''
        size = len(list(self.get_cells()))
        num = int(p * size)
        
        linked = []
        
        for i in range(0, num):
            cell = self.get_random_cell()
            neighbors = [n for n in cell.neighbors() if not cell.is_linked(n)]
            
            if len(neighbors) > 0:
                n = random.choice(neighbors)
                cell.link(n)
                
                linked.append((cell, n))
        
        return linked
    
class PolarGrid(Grid):
    def __init__(self, rows, world_map = None):
        '''rows is the number of rows. world_map is an optional world map to draw the
        maze onto.'''
        self.rows = rows
        self.grid = self.prepare_grid()
        self.configure_cells()
        self.distances = None
        self.world_map = world_map
    
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
        wall = colors.RED

        if self.world_map:
            cell_size = self.world_map.map_radius // self.rows
        else:
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
            
            # TODO replace this with pol2cart
            ax = int(inner_radius * math.cos(theta_ccw))
            ay = int(inner_radius * math.sin(theta_ccw))
            bx = int(outer_radius * math.cos(theta_ccw))
            by = int(outer_radius * math.sin(theta_ccw))
            cx = int(inner_radius * math.cos(theta_cw))
            cy = int(inner_radius * math.sin(theta_cw))
            dx = int(outer_radius * math.cos(theta_cw))
            dy = int(outer_radius * math.sin(theta_cw))
            
            if self.world_map:
                ax, ay = self.world_map.convert_coords(ax, ay)
                cx, cy = self.world_map.convert_coords(cx, cy)
                dx, dy = self.world_map.convert_coords(dx, dy)
            else:
                ax, ay = util.adjust_coords(ax, ay)
                cx, cy = util.adjust_coords(cx, cy)
                dx, dy = util.adjust_coords(dx, dy)
            
            
            if not cell.is_linked(cell.inward):
                pygame.draw.line(screen.surface, wall, (ax, ay), (cx, cy), width = 3)
            if not cell.is_linked(cell.cw):
                pygame.draw.line(screen.surface, wall, (cx, cy), (dx, dy), width = 3)

            # Draw the distance from Maxine if it's been calculated
            if (constants.DRAW_DISTANCES_FROM_MAXINE and
                self.distances and self.distances[cell] is not None):
                pos = self.get_center(cell)
                screen.draw.text(str(self.distances[cell]), pos,
                    fontname = "ds-digi.ttf", color = "white")

        # skip the bounding ellipse because it draws in the wrong place (?!)        
        #bounds = pygame.Rect(
        #    (x - constants.TORUS_INNER_WIDTH // 2, y - constants.TORUS_INNER_HEIGHT // 2),
        #    (x + constants.TORUS_INNER_WIDTH // 2, y + constants.TORUS_INNER_HEIGHT // 2))
        #pygame.draw.ellipse(screen.surface, wall, bounds, width = 3)
        
    def draw_keybindings(self, maxine_cell, screen):
        self.draw_keybinding(maxine_cell, maxine_cell.cw, '⇣', screen)
        self.draw_keybinding(maxine_cell, maxine_cell.ccw, '⇡', screen)
        self.draw_keybinding(maxine_cell, maxine_cell.inward, '⇠', screen)
        
        for i, cell in enumerate(maxine_cell.outward):
            self.draw_keybinding(maxine_cell, cell, str(i + 1), screen)
    
    def draw_keybinding(self, maxine_cell, neighbor, binding, screen):
        if neighbor is None or not maxine_cell.is_linked(neighbor):
            return
        
        pos = self.get_center(neighbor)
        
        # Convert from map coordinates to screen coordinates if necessary.
        if self.world_map:
            pos = self.world_map.convert_coords(pos[0], pos[1])
        
        screen.draw.text(binding, pos,
           fontname = 'segoeuisymbol.ttf', color = "red")

        
    def make_room_row(self, row, ccw_column, cw_column, connect_inward = False):
        for i in range(ccw_column, cw_column):
            cell1 = self[(row, i)]
            cell2 = self[(row, i + 1)]
            cell1.link(cell2)
        
        if connect_inward:
            for i in range(ccw_column, cw_column + 1):
                cell = self[(row, i)]
                cell.link(cell.inward)

    def make_room(self, inner_row, ccw_column, num_rows, num_inner_columns):
        # TODO handle the case where the number of columns doubles partway through
        for row in range(inner_row, inner_row + num_rows):
            #connect_inward = (row != inner_row)
            # Connect the inner row to the rest of the maze. GrowingTree won't do it
            connect_inward = True
            self.make_room_row(row, ccw_column,
                               ccw_column + num_inner_columns - 1, connect_inward)

    def make_rooms(self):
        self.make_room(3, 2, 3, 4)
        self.make_room(3, 8, 3, 4)
        self.make_room(3, 14, 3, 4)
        self.make_room(3, 20, 3, 4)
        
    def get_center(self, cell):
        if self.world_map:
            cell_size = self.world_map.map_radius // self.rows
        else:
            cell_size = constants.TORUS_INNER_RADIUS // self.rows        
        
        # Uses radians.
        theta        = 2 * math.pi / len(self.grid[cell.row])
        
        center_radius = (cell.row + 0.5) * cell_size
        theta_center = (cell.column + 0.5) * theta
        
        x = int(center_radius * math.cos(theta_center))
        y = int(center_radius * math.sin(theta_center))

        if not self.world_map:
            x, y = util.adjust_coords(x, y)
        
        return (x, y)

    def setup_distances_from_root(self, root):
        self.distances = root.distances(self)

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
    
    def distances_perfect(self):
        '''This is the simplified version of Dijkstra's algorithm that only
        works on perfect mazes (i.e. mazes with no loops).'''
        distances = Distances(self)
        frontier = [ self ]
        
        while frontier:
            new_frontier = []
            
            for cell in frontier:
                for linked in cell.get_links():
                    if distances[linked] is not None:
                        continue
                    distances[linked] = distances[cell] + 1
                    new_frontier.append(linked)
            frontier = new_frontier
        
        return distances
    
    def distances(self, grid):
        '''This is the complex version of Dijkstra's algorithm based on
        Wikipedia. It works for mazes with or without loops.'''
        distances = Distances(self)
        # Using a normal list because heapq doesn't support updating priorities
        q = list(grid.get_cells())
        
        # Find cell in q with minimum distance
        while len(q) != 0:
            min_dist = float('+inf')
            cell = None
            for c in q:
                dist = distances[c]
                if dist is None:
                    dist = float('+inf')
                if dist < min_dist:
                    min_dist = dist
                    cell = c
                   
            q.remove(cell)
            
            for neighbor in cell.get_links():
                if neighbor not in q:
                    continue
                
                alt = distances[cell] + 1
                dist_n = distances[neighbor]
                if dist_n is None or alt < dist_n:
                    distances[neighbor] = alt
        
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
        
class Distances:
    '''Records the distances of every cell in a grid from the "root" (you can
    choose whatever root cell you want). Has helpful methods too.'''
    def __init__(self, root):
        self.root = root
        # self.cells stores the distance from each cell to the root.
        self.cells = {}
        self.cells[root] = 0
    
    def __getitem__(self, cell):
        if cell in self.cells:
            return self.cells[cell]
        else:
            return None
    
    def __setitem__(self, cell, distance):
        self.cells[cell] = distance
        
    def get_cells(self):
        return list(self.cells.keys())
    
    def path_to(self, goal):
        current = goal
        
        breadcrumbs = Distances(self.root)
        breadcrumbs[current] = self.cells[current]
        
        while current != root:
            for neighbor in current.get_links():
                if self.cells[neighbor] < self.cells[current]:
                    breadcrumbs[neighbor] = self.cells[neighbor]
                    current = neighbor
                    break
                    
        return breadcrumbs
    
    def max(self):
        max_distance = 0
        max_cell = self.root
        
        for cell, distance in self.cells.items():
            if distance > max_distance:
                max_cell = cell
                max_distance = distance
        
        return (max_cell, max_distance)

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

class GrowingTree:
    @staticmethod
    def on(grid, function, start_at = None):
        if start_at is None:
            start_at = grid.get_random_cell()
 
        active = []
        active.append(start_at)
        
        while len(active) > 0:
            cell = function(active)
            available_neighbors = [n for n in cell.neighbors() if len(n.get_links()) == 0]
            
            if len(available_neighbors) > 0:
                neighbor = random.choice(available_neighbors)
                cell.link(neighbor)
                active.append(neighbor)
            else:
                active.remove(cell)
        
        return grid
    
    @staticmethod
    def use_random(active):
        return random.choice(active)
    
    @staticmethod
    def use_last(active):
        return active[-1]

