import random
import math
import pygame

import constants
import util
import colors
import game_object

# Grid classes

class Grid:
    '''Abstract base class of grids.'''
    def __init__(self):
        self.removed_walls = []
        self.doors = []
    
    def deadends(self):
        ret = []
        for cell in self.get_cells():
            if len(cell.links) == 1:
                ret.append(cell)
        
        return ret

    def get_row_size(self, row):
        return len(self.grid[row])

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
            
            self.removed_walls.append( (cell, neighbor) )
    
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
                
                self.removed_walls.append( (cell, n) )
        
        return linked
    
    def add_door(self, cells):
        cell, neighbor = cells
        
        self.doors.append(cells)
        self.removed_walls.remove(cells)
        
        cell.unlink(neighbor)
        
    def door_exists(self, cells):
        cell, neighbor = cells
        cells2 = (neighbor, cells)
        
        return cells in self.doors or cells2 in self.doors
        
    def open_door(self, cells):
        cell, neighbor = cells
        cells2 = (neighbor, cells)
        
        if cells in self.doors:
            self.doors.remove(cells)
        if cells2 in self.doors:
            self.doors.remove(cells2)
            
        cell.link(neighbor)
    
class PolarGrid(Grid):
    def __init__(self, rows, world_map = None):
        '''rows is the number of rows. world_map is an optional world map to draw the
        maze onto.'''
        super().__init__()
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

    def draw(self, screen, Actor):
        wall = colors.RED
        door = 'yellow'
        DRAW_BRICKS = False

        if self.world_map:
            cell_size = self.world_map.map_radius // self.rows
        else:
            cell_size = game_object.game.torus_inner_radius // self.rows        
        
        for cell in self.get_cells():
            if cell.row == 0:
                continue
                
            # Uses radians.
            theta        = 2 * math.pi / self.get_row_size(cell.row)
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
            
            # Calculate the center of each line. This has to be done after the
            # coordinates are converted so you don't get gaps between the walls.
            acx = (ax + cx) / 2
            acy = (ay + cy) / 2
            
            cdx = (cx + dx) / 2
            cdy = (cy + dy) / 2

            ac_delta_x = (cx - ax)
            ac_delta_y = (cy - ay)
            ac_bricks_angle = (180 - math.degrees(math.atan(ac_delta_y / ac_delta_x))) % 360
            
            cd_delta_x = (dx - cx)
            cd_delta_y = (dy - cy)
            if cd_delta_x == 0:
                cd_bricks_angle = 90
            else:
                cd_bricks_angle = (180 - math.degrees(math.atan(cd_delta_y / cd_delta_x))) % 360
            
            ac_length = util.distance_points((ax, ay), (cx, cy))
            cd_length = util.distance_points((cx, cy), (dx, dy))
            
            if not cell.is_linked(cell.inward):
                if DRAW_BRICKS:
                    bricks = Actor('bricks')
                    size = bricks.size
                    bricks.scale = ac_length / size[0]
                    bricks.center =  (acx, acy)
                    bricks.angle = ac_bricks_angle
                    bricks.draw()
                else:
                    link1 = (cell, cell.inward)
                    link2 = (cell.inward, cell)
                    if link1 in self.doors or link2 in self.doors:
                        pygame.draw.line(screen.surface, door, (ax, ay), (cx, cy), width = 3)
                    else:
                        pygame.draw.line(screen.surface, wall, (ax, ay), (cx, cy), width = 3)
                
                # Draw a white point in the center of the line to check the math
                #pygame.draw.circle(screen.surface, 'white', (acx, acy), 1)
            if not cell.is_linked(cell.cw):
                if DRAW_BRICKS:
                    bricks = Actor('bricks')
                    size = bricks.size
                    bricks.scale = cd_length / size[0]
                    bricks.center =  (cdx, cdy)
                    bricks.angle = cd_bricks_angle
                    bricks.draw()
                else:
                    link1 = (cell, cell.cw)
                    link2 = (cell.cw, cell)
                    if link1 in self.doors or link2 in self.doors:
                        pygame.draw.line(screen.surface, door, (cx, cy), (dx, dy), width = 3)
                    else:
                        pygame.draw.line(screen.surface, wall, (cx, cy), (dx, dy), width = 3)

                #pygame.draw.circle(screen.surface, 'white', (cdx, cdy), 1)

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
        if neighbor is not None and (maxine_cell.is_linked(neighbor) 
                or self.door_exists((maxine_cell, neighbor))):
        
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
            cell_size = game_object.game.torus_inner_radius // self.rows        
        
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

    def get_angle(self, cell):
        '''Get the angle of cell. Uses degrees. Starts at the top and goes clockwise.'''
        theta        = 360 / self.get_row_size(cell.row)
        ret = (cell.column) * theta + 90
        ret = ret % 360
        return ret

    def get_cells_near_center(self, distance):
        rows = self.get_rows()[0 : distance + 1]
        cells = set()
        for row in rows:
            for cell in row:
                cells.add(cell)
        return cells
    
    def get_random_cell_near_center(self, distance):
        cells = list(self.get_cells_near_center(distance))
        return random.choice(cells)

    def get_cells_near_cell(self, cell, distance):
        # TODO see if this takes too long and cache the result for making multiple monsters
        cells = cell.distances(self, distance)
        return cells
        
    def get_random_cell_near_cell(self, cell, distance):
        cells = list(self.get_cells_near_cell(cell, distance))
        return random.choice(cells)

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
        del self.links[cell]
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
    
    def distances(self, grid, max_dist = None):
        '''This is the complex version of Dijkstra's algorithm based on
        Wikipedia. It works for mazes with or without loops.
        
        If you don't specify max_dist, you get a Distances object with
        every distance in the grid. If you specify it, you get a set of
        cells within that distance.'''
        distances = Distances(self)
        nearby_cells = set()
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
            
            if max_dist and min_dist > max_dist:
                return nearby_cells
            
            for neighbor in cell.get_links():
                if neighbor not in q:
                    continue
                
                alt = distances[cell] + 1
                dist_n = distances[neighbor]
                if dist_n is None or alt < dist_n:
                    distances[neighbor] = alt
                    
                    if max_dist and distances[neighbor] <= max_dist:
                        nearby_cells.add(neighbor)
        
        if max_dist:
            return nearby_cells
        else:
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

