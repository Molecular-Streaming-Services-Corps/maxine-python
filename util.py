import numpy as np
import math

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
def spiral(gap, theta):
    r = gap * theta
    cart = pol2cart(r, theta)
    return cart
    
