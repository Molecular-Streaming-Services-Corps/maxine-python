import numpy as np

VIDEO_WIDTH = 640
VIDEO_HEIGHT = 360

def make_ellipse():
    '''Only needs to be called once.'''
    x = np.arange(0, VIDEO_WIDTH)
    y = np.arange(0, VIDEO_HEIGHT)
    y_grid, x_grid = np.meshgrid(y, x)

    rx = VIDEO_WIDTH/2
    ry = VIDEO_HEIGHT/2
    xc, yc = (rx, ry)
    ellipse = (x_grid-xc)**2/rx**2 + (y_grid-yc)**2/ry**2 < 1

    return ellipse

def make_black_image():
    black_image = np.zeros((VIDEO_WIDTH, VIDEO_HEIGHT, 3), dtype='uint8')
    return black_image

def make_green_image():
    green_image = np.array(black_image)
    
    green_image[:, :, 1] = 255

    return green_image

def composite(mask, bg, fg):
    ret = np.array(black_image)
    for c in range(0, 3):
        ret[:,:,c] = np.where(mask, fg[:,:,c], bg[:,:,c])
    return ret

def tint(image, color):
    for i in range(0, 3):
        image[:,:,i] = image[:,:,i] * (color[i] / 255)

ellipse = make_ellipse()
black_image = make_black_image()
green_image = make_green_image()

