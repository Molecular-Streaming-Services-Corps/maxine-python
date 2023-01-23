import numpy as np

import constants

def make_ellipse(ret = None):
    '''Only needs to be called once.'''
    if ret:
        return ret
        
    x = np.arange(0, constants.VIDEO_WIDTH)
    y = np.arange(0, constants.VIDEO_HEIGHT)
    y_grid, x_grid = np.meshgrid(y, x)

    rx = constants.VIDEO_WIDTH/2
    ry = constants.VIDEO_HEIGHT/2
    xc, yc = (rx, ry)
    ellipse = (x_grid-xc)**2/rx**2 + (y_grid-yc)**2/ry**2 < 1

    ret = ellipse
    return ellipse

def make_black_image(ret = None):
    if ret:
        return ret

    black_image = np.zeros((constants.VIDEO_WIDTH, constants.VIDEO_HEIGHT, 3), dtype='uint8')
    
    ret = black_image
    return black_image

def make_green_image(ret = None):
    if ret:
        return ret

    green_image = np.array(make_black_image())
    
    green_image[:, :, 1] = 255

    ret = green_image
    return green_image

def composite(mask, bg, fg):
    ret = np.array(make_black_image())
    for c in range(0, 3):
        ret[:,:,c] = np.where(mask, fg[:,:,c], bg[:,:,c])
    return ret

def tint(image, color):
    for i in range(0, 3):
        image[:,:,i] = image[:,:,i] * (color[i] / 255)

