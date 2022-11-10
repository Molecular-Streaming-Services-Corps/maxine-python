import math

import util
import constants

class WorldMap:
    def __init__(self, map_width, map_height, viewport_width, viewport_height):
        self.map_width = map_width
        self.map_height = map_height
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height

class LogarithmicWorldMap(WorldMap):
    def __init__(self):
        self.map_radius = 1000

    def convert_coords(self, map_x, map_y):
        '''Converts from map coordinates to on-screen coordinates.'''
        map_r, map_theta = util.cart2pol(map_x, map_y)
        # Converts map radiuses between 0 and 1000 into nonlinear radiuses
        # between 0 and 1
        viewport_r_log = math.log(map_r / self.map_radius * 32 + 1, 32)
        viewport_r = viewport_r_log * constants.TORUS_INNER_RADIUS
        # The angle (theta) remains the same.
        # x and y are in screen coordinates
        x, y = util.pol2cart(viewport_r, map_theta)
        x, y = util.adjust_coords(x, y)
        
        return x, y
    
    def convert_scale(self, map_x, map_y):
        map_r, map_theta = util.cart2pol(map_x, map_y)
        log = math.log(map_r / self.map_radius * 32 + 1, 32)
        scale = 1 - log
        return scale
    
    def calculate_grid_with_map_coords(self):
        increment = self.map_radius // 10
    
        # Get the vertical line segments
        lines = []
        for map_x in range(-self.map_radius, +self.map_radius, increment):
            for map_y in range(-self.map_radius, +self.map_radius, increment):
                line = ((map_x, map_y), (map_x, map_y + increment))
                lines.append(line)
                
        # Get the horizontal line segments
        for map_x in range(-self.map_radius, +self.map_radius, increment):
            for map_y in range(-self.map_radius, +self.map_radius, increment):
                line = ((map_x, map_y), (map_x + increment, map_y))
                lines.append(line)

        return lines    
    
    def draw_grid(self, screen):
        map_lines = self.calculate_grid_with_map_coords()
        
        # Convert them to on-screen lines
        screen_lines = []
        for line in map_lines:
            start, end = line
            start_x, start_y = start
            end_x, end_y = end
            
            screen_start = self.convert_coords(start_x, start_y)
            screen_end = self.convert_coords(end_x, end_y)
            screen_line = (screen_start, screen_end)
            screen_lines.append(screen_line)

        print(screen_lines)

        for start, end in screen_lines:
            screen.draw.line(start, end, color = 'red')
