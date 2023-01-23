import cv2
import numpy as np
import pygame

import image_ops
import constants
import game_object

# Code for displaying the microscope footage inside the signal ring
video = None
restart_video = True
frame = 0
surf = None
video_image = None
def update_video():
    global frame, video, restart_video, video_image, surf
    frame += 1

    if restart_video:
        video = cv2.VideoCapture(constants.VIDEO_FILE)
        restart_video = False

    # Get one frame as an OpenCV image
    prev_image = video_image
    if frame % 2 in [0]:
        success, video_image = video.read()
    else:
        success = True
    if success:
        if video_image is None:
            return
            
        constants.VIDEO_HEIGHT, constants.VIDEO_WIDTH, _ = video_image.shape
            
        # Change it to our format
        img = np.array(video_image)
        img = img.transpose([1, 0, 2])
        img = img[:,:,::-1]

        light_purple = 203, 195, 227
        bright_purple = 191, 64, 191
        image_ops.tint(img, bright_purple)
        display = image_ops.composite(image_ops.make_ellipse(), 
            image_ops.make_green_image(), img)
        
        # Get pygame surface (it's created from an array with no alpha channel
        # so it has no alpha channel itself).
        surf = pygame.surfarray.make_surface(display)
        surf.set_colorkey((0, 255, 0))
        surf = pygame.transform.scale(surf, 
            (game_object.game.ring_width, game_object.game.ring_height))
    else:
        restart_video = True    
        frame = 0

def draw_video(screen):
    global surf
    
    if surf:
        x = (constants.WIDTH - game_object.game.ring_width) // 2
        y = (constants.HEIGHT - game_object.game.ring_height) // 2
        screen.blit(surf, (x, y))

