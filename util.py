import numpy as np
import math

import constants

def process_joystick_data(joystick_data):
    binary_string = bin(joystick_data)[2:]
    return process_joystick_string(binary_string)

def process_joystick_string(binary_string):
    button_names = ['up', 'down', 'left', 'right', 'b1', 'b2']
    all_buttons = ['js1_' + b for b in button_names] + ['not_used'] * 2 + ['js2_' + b for b in button_names] + ['not_used'] * 2
    
    pressed = []

    for i, bit in enumerate(reversed(binary_string)):
        if bit == '0':
            button = all_buttons[i]
            if button != 'not_used':
                pressed.append(button)
                
    return pressed

# Polar coordinate functions (in degrees)
def cart2pol(x, y):
    r = np.sqrt(x**2 + y**2)
    theta = np.degrees(np.arctan2(y, x))
    return(r, theta)

def pol2cart(r, theta):
    x = r * np.cos(np.radians(theta))
    y = r * np.sin(np.radians(theta))
    return(x, y)
    
# Distance between two points (as tuples)
def distance_points(pa, pb):
    dx = abs(pa[0] - pb[0])
    dy = abs(pa[1] - pb[1])

    return math.sqrt(dx ** 2 + dy ** 2)

# Calculate a spiral
def spiral(gap, rotation, theta):
    r = gap * theta
    cart = pol2cart(r, theta + rotation)
    return cart

class SpiralState:
    '''For making monsters move in a spiral'''
    def __init__(self, gap, rotation, theta, step_degrees, center_pos, aspect_ratio):
        self.gap = gap
        self.rotation = rotation
        self.theta = theta
        self.step_degrees = step_degrees
        self.center_pos = center_pos
        self.aspect_ratio = aspect_ratio
        
        self.update()
        
    def update(self):
        self.pos = spiral(self.gap, self.rotation, self.theta)
        self.pos = (self.pos[0] * self.aspect_ratio, self.pos[1])
        self.pos = (self.pos[0] + self.center_pos[0], self.pos[1] + self.center_pos[1])
        self.angle = 360 - ((self.theta + self.rotation) % 360)
        self.theta -= self.step_degrees
        
def adjust_coords(x, y):
    # Stretch in the x dimension to match the greater width of the ellipse,
    # and then add the center to the Cartesian coordinates
    WIDTH_TO_HEIGHT_RATIO = constants.RING_WIDTH / constants.RING_HEIGHT

    (x, y) = (WIDTH_TO_HEIGHT_RATIO * x, y)
    (x, y) = (x + constants.CENTER[0], y + constants.CENTER[1])
    return (x, y)

