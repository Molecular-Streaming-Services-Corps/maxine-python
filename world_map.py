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
    '''Circular world map with a default radius of 1000. On screen, objects shrink
    and move slower as they get nearer the edge of the map. Specifically they
    move onscreen the logarithm of the distance they move on the map.'''
    def __init__(self, game, radius = 1000):
        self.map_radius = radius
        self.game = game

    def convert_coords(self, map_x, map_y):
        '''Converts from map coordinates to on-screen coordinates.'''
        # Move all objects so that Maxine is in the center of the screen.
        # When Maxine moves to the right, the amount of map area that has
        # to fit on the left side of the ellipse is increased. So first
        # calculate that amount.
        if self.game.maxine.map_x == 0:
            map_side_width = self.map_radius
        else:
            map_side_width = self.map_radius + abs(self.game.maxine.map_x)

        if self.game.maxine.map_y == 0:
            map_side_height = self.map_radius
        else:
            map_side_height = self.map_radius + abs(self.game.maxine.map_y)
        
        map_x = (map_x - self.game.maxine.map_x) / map_side_width
        map_y = (map_y - self.game.maxine.map_y) / map_side_height
        
        map_r, map_theta = util.cart2pol(map_x, map_y)
        # Converts map radiuses between 0 and 1000 into nonlinear radiuses
        # between 0 and 1
        viewport_r_log = math.log(map_r * 32 + 1, 32)
        viewport_r = viewport_r_log * self.game.torus_inner_radius
        # The angle (theta) remains the same.
        # x and y are in screen coordinates
        x, y = util.pol2cart(viewport_r, map_theta)
        x, y = util.adjust_coords(x, y)
        
        return x, y
    
    def convert_scale(self, actor, images):
        # Old approach, doesn't work with the map shrinking on one side
        #map_r, map_theta = util.cart2pol(map_x, map_y)
        #log = math.log(map_r / self.map_radius * 32 + 1, 32)
        #scale = 1 - log
        
        # New approach: calculate the height of the object based on
        # convert_coords.
        mx, my = actor.map_x, actor.map_y
        img = getattr(images, actor.images[0])
        width, height = img.get_size()
        
        # Start with map coordinates.
        top = my - height
        bottom = my + height
        diff = abs(top - bottom)
        
        # Then screen coordinates.
        screen_top = self.convert_coords(mx, top)[1]
        screen_bottom = self.convert_coords(mx, bottom)[1]
        screen_diff = abs(screen_bottom - screen_top)
        
        scale = screen_diff / diff
        
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
            
            # Don't draw the parts of the grid that are beyond the edge of the circle.
            center = (0, 0)
            if (util.distance_points(start, center) > 1000 or
                util.distance_points(end, center) > 1000):
                continue
            
            screen_start = self.convert_coords(start_x, start_y)
            screen_end = self.convert_coords(end_x, end_y)
            screen_line = (screen_start, screen_end)
            screen_lines.append(screen_line)

        for start, end in screen_lines:
            screen.draw.line(start, end, color = 'red')
