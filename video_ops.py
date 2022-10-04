import cv2
import numpy as np
import pygame

import image_ops

# Code for displaying the microscope footage inside the signal ring
video = None
restart_video = True
frame = 0
surf = None
video_image = None
def update_video(RING_WIDTH, RING_HEIGHT):
    global frame, video, restart_video, video_image, surf
    frame += 1

    if restart_video:
        video = cv2.VideoCapture('cells.mp4')
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
            
        # Change it to our format
        img = np.array(video_image)
        img = img.transpose([1, 0, 2])
        img = img[:,:,::-1]

        light_purple = 203, 195, 227
        bright_purple = 191, 64, 191
        image_ops.tint(img, light_purple)
        display = image_ops.composite(image_ops.ellipse, image_ops.green_image, img)
        
        # Get pygame surface (it's created from an array with no alpha channel
        # so it has no alpha channel itself).
        surf = pygame.surfarray.make_surface(display)
        surf.set_colorkey((0, 255, 0))
        surf = pygame.transform.scale(surf, (RING_WIDTH, RING_HEIGHT))
    else:
        restart_video = True    
        frame = 0

def draw_video(screen, RING_WIDTH, RING_HEIGHT, WIDTH, HEIGHT):
    global surf
    
    if surf:
        x = (WIDTH - RING_WIDTH) // 2
        y = (HEIGHT - RING_HEIGHT) // 2
        screen.blit(surf, (x, y))

