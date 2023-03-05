import numpy as np
import math

import constants
import game_object

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
    # Stretch in the x dimension to match the greater width of the torus,
    # and then add the center to the Cartesian coordinates
    ga = game_object.game
    WIDTH_TO_HEIGHT_RATIO = ga.torus_inner_width / ga.torus_inner_height

    (x, y) = (WIDTH_TO_HEIGHT_RATIO * x, y)
    (x, y) = (x + constants.CENTER[0], y + constants.CENTER[1])
    return (x, y)

def adjust_coords_ring(x, y):
    '''Used by the signal ring. It's based on the signal ring's size
    rather than the torus's size.'''
    ga = game_object.game
    WIDTH_TO_HEIGHT_RATIO = ga.ring_width / ga.ring_height

    (x, y) = (WIDTH_TO_HEIGHT_RATIO * x, y)
    (x, y) = (x + constants.CENTER[0], y + constants.CENTER[1])
    return (x, y)

def all_zeros(a):
    are_zeros = a == 0
    az = np.all(are_zeros)
    return az and len(a)

# Memoized class from the Python Decorator Library
import collections
import functools

class memoized(object):
   '''Decorator. Caches a function's return value each time it is called.
   If called later with the same arguments, the cached value is returned
   (not reevaluated).
   '''
   def __init__(self, func):
      self.func = func
      self.cache = {}
   def __call__(self, *args):
      if not isinstance(args, collections.abc.Hashable):
         # uncacheable. a list, for instance.
         # better to not cache than blow up.
         return self.func(*args)
      if args in self.cache:
         return self.cache[args]
      else:
         value = self.func(*args)
         self.cache[args] = value
         return value
   def __repr__(self):
      '''Return the function's docstring.'''
      return self.func.__doc__
   def __get__(self, obj, objtype):
      '''Support instance methods.'''
      return functools.partial(self.__call__, obj)

