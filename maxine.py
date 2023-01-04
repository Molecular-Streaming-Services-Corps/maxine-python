#!/usr/bin/env python
# Installed packages.
import pgzrun
from pgzhelper import *
import pygame
import numpy as np
import logging
import time

# Builtin packages.
import random
import threading

# Local packages.
import data
import util
import lilith_client
import serialization
import music_ops
import video_ops
import graphs
import mazes
import constants
import colors
import components
import game_object
import controls_object
import world_map

# Set up logger for this module
logger = logging.getLogger('maxine')
logger.setLevel(logging.DEBUG)
import sys
handler = logging.StreamHandler(sys.stdout)
handler.formatter = logging.Formatter('%(asctime)s  %(name)s %(levelname)s: %(message)s')
logger.addHandler(handler)

TITLE = 'Maxine\'s µMonsters'
WIDTH = constants.WIDTH
HEIGHT = constants.HEIGHT

game = game_object.Game(Actor, sounds, images, clock)
game_object.game = game

#graph_type = 'heatmap'
graph_type = 'line_ring'
#graph_type = 'boxes_ring'

game_state = 'title' # becomes 'playing', 'won' or 'lost'
level = 1
switch_level_timeout = 120
playing_music = True

'''Vertical Line Ring'''
vlr = None

# Temporary development tool
dev_control = None

spore_count = 0

maze = None

# Logarithmic World Map
lwm = None

controls = None

challenger_image = Actor('challengeplayer')
challenger_image.center = (40, 160)

console_image = Actor('consoleplayer')
console_image.center = (40, 220)

# Represents data from a stored file.
d = None

rotation = 0

helpbutton = Actor('helpbutton')
helpbutton.images = ['helpbutton']
helpbutton.scale = 0.26
helpbutton.right = 1400
helpbutton.top = 18

data_number = 0
data_text= 'Translocations'

dataglobe = Actor('dataglobe')
dataglobe.right = 1800
dataglobe.top = 268

databutton = Actor('databutton')
databutton.right = 1785
databutton.top = 410

brainpod = Actor('brainpod1')
brainpod.images = ('brainpod1','brainpod2','brainpod3','brainpod4')
brainpod.scale = 1
brainpod.bottom = 900
brainpod.left = 0
brainpod.fps = 4

brainalert = Actor('brainalert')
brainalert.scale = .75
brainalert.top = 550
brainalert.left = 160

chatwindow = Actor('chatwindow')
chatwindow.bottom = 550
chatwindow.left = 0

peoplebutton = Actor('peoplebutton')
peoplebutton.scale = 0.4
peoplebutton.left = 10
peoplebutton.top = 10

audioselector = Actor('audioselector')
audioselector.left = 100

skirt = Actor('skirt')
skirt.center = (WIDTH/2, HEIGHT-38)

def draw():
    global rotation, dev_control
    global challenger_image, console_image
    global game, lwm, maze
    global game_state
    
    if game_state == 'title':
        game.draw_title_screen(screen)
        return
    
    draw_living_background()

    if game.draw_panels:
        skirt.draw()
    
    # Draw the microscope video in front of the background and behind the signal ring
    video_ops.draw_video(screen)
    
    graphs.draw_torus(screen, images)
    
    if graph_type == 'line_ring':
        vlr.draw()
    else:
        graphs.draw_graph(i, d, graph_type, screen, STANDALONE)
        
    # Dragon Tyrant level
    if level in [6, 7, 8] and maze:
        maze.draw(screen, Actor)
        
        if constants.DRAW_CONTROLS and hasattr(game.maxine, 'gridnav'):
            maze.draw_keybindings(game.maxine.gridnav.in_cell, screen)
        
    if level == 7 and lwm and constants.DRAW_GRID:
        lwm.draw_grid(screen)
        
    if game.draw_panels:
        helpbutton.draw()
        dataglobe.draw()
        databutton.draw()
        brainpod.draw()
        brainalert.draw()
        chatwindow.draw()
        peoplebutton.draw()
        audioselector.draw()

        # Now we draw the controls for both players.
        controls.draw()
    
    if dev_control:
        dev_control.draw()

    #Draw Player Images
    if game.draw_panels:
        challenger_image.draw()    
        console_image.draw()

        screen.draw.text('instantLife: ' + str(game.challenger_score), (90, 160))
        screen.draw.text('kemmishTree: ' + str(game.console_score), (90, 220))

        screen.draw.text(str(data_number), center = (1655, 320), fontname = "ds-digi.ttf", fontsize = 50, color = "red")
        screen.draw.text(str(data_text), center = (1655, 400), fontname = "ds-digi.ttf", fontsize = 20, color = "red")

        game.draw(screen)

    # Draw Cannon
    if game.cannon_in_level:
        for cannon in game.ranged_monsters:
            cannon.draw()

    # Draw Maxine or the boom
    game.maxine.draw()
    
    for monster in game.spiraling_monsters:
        monster.draw()
    for monster in game.bouncing_monsters:
        monster.draw()
    for monster in game.walking_monsters:
        monster.draw()
    for monster in game.dead_monsters:
        monster.draw()
    for monster in game.maze_monsters:
        monster.draw()
    for item in game.items:
        item.draw()
        
    for p in game.projectiles:
        p.draw()

    # Only use in Level 8 Battle Royale
    for m in game.other_maxines:
        m.draw()

    # Draw the signal ring.
    RED = (200, 0, 0)
    ring_rect = Rect((constants.CENTER[0] - game.ring_width / 2, constants.CENTER[1] - game.ring_height / 2), 
                     (game.ring_width, game.ring_height))
    pygame.draw.ellipse(screen.surface, RED, ring_rect, width = 1)
    
    if game.draw_spirals:
        # Draw spirals to indicate where the monsters will move
        rotation += 1
        draw_spiral(rotation + 0, colors.WHITE)
        draw_spiral(rotation + 180, colors.WHITE)

    if PLAYER == 'maxine':
        # Draw the victory or gameover graphics (or nothing if the game is still going).
        if game_state == 'lost':
            gameover = Actor('gameover')
            gameover.pos = constants.CENTER
            gameover.draw()
        elif game_state == 'won':
            victory = Actor('victory')
            victory.pos = constants.CENTER
            victory.draw()

def draw_living_background():
    global step_count
    
    tile_size = 144
    
    offset = step_count % tile_size

    for x in range(-tile_size, WIDTH, tile_size):
        for y in range(-tile_size, HEIGHT, tile_size):
            screen.blit('background_living_tissue', (x + offset, y + offset))

def draw_metal_background():
    surface = getattr(images, 'bg_cut')
    surface = pygame.transform.scale(surface, (WIDTH, HEIGHT))
    screen.blit(surface, (0, 0))

i = 0

def draw_spiral(rotation, color):
    global lwm, game
    
    GAP = 0.5
    
    if lwm:
        MAX_THETA = lwm.map_radius * 2
    else:
        MAX_THETA = game.torus_inner_height
    STEP_DEGREES = 10
    
    for theta in range(0, MAX_THETA, STEP_DEGREES):
        (x, y) = util.spiral(GAP, rotation, theta)
        if lwm:
            (x, y) = lwm.convert_coords(x, y)
        else:
            (x, y) = util.adjust_coords(x, y)
        screen.draw.filled_circle((x, y), 1, color)

step_count = 0
space_pressed_before = False
button_pressed_before = False
def update():
    global i, step_count, d, space_pressed_before, button_pressed_before
    global logger
    global playing_music
    global sg, cg, vlr
    global controls
    global data_number
    global game

    if keyboard.q:
        import sys; sys.exit(0)
        
    if game_state == 'title':
        if keyboard.space:
            start_next_level()
            update()
        
        return

    step_count += 1
    if step_count % 10 == 0:
        i += 1
        #print('update(): i:', i)

    # Update the microscope video
    video_ops.update_video()

    if not vlr:
        if LIVE:
            vlr = graphs.VerticalLineRing(screen, game, LIVE, 20 * 5)
        else:
            vlr = graphs.VerticalLineRing(screen, game, LIVE, constants.NUM_BOXES)
    
    if not controls:
        controls = controls_object.Controls(Actor, serializer, LIVE, PLAYER, screen)
    
    brainpod.animate()
    
    game.update()
    
    # Advance the datafile and make a monster appear on a spike.
    # If we're in STANDALONE mode, a timer will make the monster appear.
    if DATADIR:
        d.get_one_frame_current()

        last_second = d.get_last_n_samples(100000)
        game.rms_last_second = data.Data.rms(last_second)

        frame = d.get_frame()
                
        last_n_samples = d.get_last_n_samples(1667*constants.NUM_BOXES)
        vlr.give_samples(last_n_samples)

        maxes_mins = data.Data.calculate_maxes_and_mins(last_n_samples, 1667)
        sudden_change = data.Data.end_spike_exists(maxes_mins)
        deviation_from_mean = data.Data.statistical_end_spike_exists(last_n_samples, constants.NUM_BOXES)
        
        spike_exists = sudden_change and deviation_from_mean
        
        if spike_exists:
            controls.sg.set_frame(frame)
        
        # The length of the frame must be 1667. At the end of the data it will
        # be less, so we skip the last partial frame.
        if controls.corner_display == 'continuous_graph' and frame is not None and len(frame) == 1667:
            controls.cg.set_frame(frame)
            
        if spike_exists:
            vlr.add_spike()
            data_number += 1

        vlr.advance_n_frames(1)
        
        if playing_music:
            #music_ops.current_to_frequency(frame)
            #music_ops.current_to_volume(frame)
            music_ops.stats_to_frequency(maxes_mins)
        
        d.advance_frame()
        
        if PLAYER == 'maxine' and spike_exists:
            add_cell()
    elif LIVE:
        MONSTERS_PER_SPIKE = 1
        #lilith_client.request_data(lilith_client.ws, 1)
    
        spikes = d.load_received_samples_and_count_spikes()
    
        last_second = d.get_last_n_frames(100000 // 5120)
        game.rms_last_second = data.Data.rms(last_second)

        frame = d.get_frame()
        
        if spikes > 0:
            controls.sg.set_frame(frame)
    
        if controls.corner_display == 'continuous_graph' and frame is not None and len(frame):
            controls.cg.set_frame(frame)
    
        if PLAYER == 'maxine':
            for i in range(0, spikes * MONSTERS_PER_SPIKE):
                add_cell() 
                
        # 5 seconds at 20 FPS
        last_n_samples = d.get_last_n_frames(20 * 5)
        vlr.give_samples(last_n_samples)
        
        data_number += spikes
        
        booleans = d.get_recent_frames_contain_spikes()
        for b in booleans:
            vlr.advance_n_frames(1)
            if b:
                vlr.add_spike()
        
        if playing_music:
            maxes_mins = data.Data.calculate_maxes_and_mins(last_n_samples, 5120)
            #music_ops.current_to_frequency(frame)
            #music_ops.current_to_volume(frame)
            music_ops.stats_to_frequency(maxes_mins)

        #num_frames_just_received = d.get_num_frames_just_received()
        #vlr.advance_n_frames(num_frames_just_received)
    elif STANDALONE:
        vlr.give_samples([])   

    if PLAYER == 'maxine':
        if game_state in ['playing', 'won']:
            update_for_maxine_player()
        
            # Send updates to the other player    
            if MULTIPLAYER:
                wrapper = game.save_arena_to_dict()
                json_string = serializer.save_dict_to_string(wrapper)
                lilith_client.send_status(json_string)
    else:
        update_for_console_player()

        if MULTIPLAYER:
            wrapper = controls.save_to_dict()
            json_string = serializer.save_dict_to_string(wrapper)
            lilith_client.send_status(json_string)

    # Process updates only from the other player.
    state_d_list = lilith_client.consume_latest_samples(lilith_client.state_q)
    for state_data in state_d_list:
        wrapper = serializer.load_dict_from_string(state_data.json_string)
        ty = wrapper['type']
        if ty == 'controls' and PLAYER == 'maxine':
            controls.load_from_dict(wrapper)
            logger.debug('loaded controls state from the internet')
        elif ty == 'maxine' and PLAYER == 'console':
            game.load_arena_from_dict(wrapper)
            logger.debug('loaded arena state from the internet')

pressed_before = set()
def update_for_console_player():
    '''Allows the console player to use either the joystick or the keyboard
    (for testing) to manipulate the onscreen controls.'''
    global pressed_before, controls

    controls.update()

    # Determine the list of pressed joystick switches
    if LIVE:
        pressed = d.pressed
    elif DATADIR:
        joystick_binary = d.get_one_frame_joystick()
        pressed = util.process_joystick_data(joystick_binary)
        #print(step_count, joystick_binary, pressed)
    else:
        # In standalone mode, we say no joystick buttons are pressed.
        pressed = []

    # Equivalent joystick and keyboard controls.
    on = {}
    on['left'] = 'js1_left' in pressed or keyboard.left
    on['right'] = 'js1_right' in pressed or keyboard.right
    on['up'] = 'js1_up' in pressed or keyboard.up
    on['down'] = 'js1_down' in pressed or keyboard.down
    on['button'] = 'js1_b1' in pressed or keyboard.space

    # See if each switch went down in this frame.
    # This allows you to make controls that only respond one time for each time the switch
    # is pressed.
    pressed_just_now = set()
    for switch_name in on.keys():
        check_pressed_just_now(switch_name, on, pressed_before, pressed_just_now)

    # Finally respond to the switches/keys that have been turned on this frame.
    if not on['button']:
        if 'up' in pressed_just_now:
            controls.select_up()
        elif 'down' in pressed_just_now:
            controls.select_down()
    
    # Some controls only respond the moment the button is pressed.
    if 'button' in pressed_just_now:
        controls.push()

    # In contrast, allow the player to press and hold the button while pressing
    # left and right.
    if on['button']:        
        if 'left' in pressed_just_now:
            controls.push_left()
        elif 'right' in pressed_just_now:
            controls.push_right()

    # Some of the controls respond continuously while left or right is pressed.
    if on['button']:
        if on['left']:
            controls.hold_left()
        elif on['right']:
            controls.hold_right()
        elif on['up']:
            controls.hold_up()
        elif on['down']:
            controls.hold_down()

def check_pressed_just_now(switch_name, on, pressed_before, pressed_just_now):
    if on[switch_name]:
        if not switch_name in pressed_before:
            pressed_before.add(switch_name)
            pressed_just_now.add(switch_name)
    else:
        if switch_name in pressed_before:
            pressed_before.remove(switch_name)
    
def update_for_maxine_player():
    global game, game_state, controls, switch_level_timeout
    global spore_count
    # This will update the images used on the controls. It won't send any duplicate signals to the server.
    controls.update()

    game.maxine.animate()

    # Move Maxine.
    # s is Maxine's speed per frame.
    s = 6 * constants.SPEED
    
    if game.maxine.alive and level not in [6, 7, 8]:
        prev_pos = game.maxine.pos

        # Put Maxine back into neutral position when she's not moving.
        game.maxine.images = ['maxine_neutral']

        # Allow the user to use either the keyboard or the joystick    
        if keyboard.left:
            game.maxine.left -= s
            game.maxine.images = ['maxine_left']
        elif keyboard.right:
            game.maxine.left += s
            game.maxine.images = ['maxine_right']
        if keyboard.up:
            game.maxine.top -= s
            game.maxine.images = ['maxine_up']
        elif keyboard.down:
            game.maxine.bottom += s
            game.maxine.images = ['maxine_down']
            
        # The old controls.
        #if keyboard.space:
        #    if not space_pressed_before:
        #        space_pressed_before = True
        #        controls.check()
        #else:
        #    space_pressed_before = False
        
        # Now we have collide_pixel
        # Detect if Maxine gets too close to the pore. (She'll explode!)
        #dist = maxine.distance_to(pore)
        #if dist < 50:
        #    kill_maxine()
        if (game.maxine.collide_pixel(game.pore) or 
            (game.cannon_in_level and game.maxine.collide_pixel(game.cannon))):
            game.kill_maxine()
        
        if point_outside_signal_ring(game.maxine.center):
            game.maxine.pos = prev_pos

    # Update Maxine's position onscreen after she moves on the maze.
    if level == 6:
        # This is necessary because of the moment that the level is 6 but it hasn't been initialized yet.
        if hasattr(game.maxine, 'gridnav'):
            gn = game.maxine.gridnav
            gn.update()
            game.maxine.center = gn.get_location()
            
            if gn.just_moved:
                maze.setup_distances_from_root(gn.in_cell)

            # Update sprite
            game.maxine.images = ['maxine_' + gn.sprite_direction]
            
    # Move Maxine on the Logarithmic Map
    if level in [7, 8] and lwm:
        FREELY_MOVING = False
        if FREELY_MOVING:
            if keyboard.left:
                game.maxine.map_x -= s
            elif keyboard.right:
                game.maxine.map_x += s
            if keyboard.up:
                game.maxine.map_y -= s
            elif keyboard.down:
                game.maxine.map_y += s

        game.maxine.center = constants.CENTER
        # Code to move Maxine around on the screen according to the map
        #game.maxine.center = lwm.convert_coords(game.maxine.map_x, game.maxine.map_y)
        #game.maxine.scale = lwm.convert_scale(game.maxine.map_x, game.maxine.map_y)

        if hasattr(game.maxine, 'gridnav'):
            gn = game.maxine.gridnav
            gn.update()
            game.maxine.map_x, game.maxine.map_y = gn.get_location()
            
            if gn.just_moved:
                maze.setup_distances_from_root(gn.in_cell)
                
            # Update sprite
            game.maxine.images = ['maxine_' + gn.sprite_direction]
    
    # Code to give other Maxines a location
    if level == 8 and lwm:
        for m in game.other_maxines:
            if hasattr(m, 'gridnav'):
                gn = m.gridnav
                gn.update()
                m.map_x, m.map_y = gn.get_location()
                
                m.center = lwm.convert_coords(m.map_x, m.map_y)
                m.scale = lwm.convert_scale(m, images)

    # Cannon Behavior
    if level in [3, 4, 5]:
        cannon = game.cannon
        cannon.animate()
        cannon.spore_timeout -= 4
        if cannon.spore_timeout <= 0 and cannon.distance_to(game.maxine) > 100:
            cannon.spore_timeout = get_spore_timeout()
            if game.cannon_shooting:
                spore_count += 1
                make_cannon_spore()  

    # Process spiraling monsters
    if level in [1, 3]:
        sm_to_blow_up = set()
        for monster in game.spiraling_monsters:
            monster.animate()
            
            # Move along the spiral
            ss = monster.spiral_state
            ss.update()
            monster.pos = ss.pos
            monster.angle = (ss.angle + 90) % 360
            
            # Blow up the monster when it gets to the center for now
            if game.cannon_in_level:
                if monster.collide_pixel(game.cannon):
                    sm_to_blow_up.add(monster)
            else:
                if util.distance_points(monster.center, constants.CENTER) < 20:
                    sm_to_blow_up.add(monster)

            # Blow up monsters that collide with Maxine
            if game.maxine.collide_pixel(monster):
                sm_to_blow_up.add(monster)
                
                game.reward_maxine()
                
            # Spawn a spore if we are far enough from Maxine and time is up
            monster.spore_timeout -= 1
            if monster.spore_timeout <= 0 and monster.distance_to(game.maxine) > 300:
                monster.spore_timeout = get_spore_timeout()
                make_spore(monster)
                spore_count += 1

        for monster in sm_to_blow_up:
            game.spiraling_monsters.remove(monster)
            game.dead_monsters.add(monster)
            #monster.images = game.boom_images()
            #monster.fps = 30
            #monster.scale = 0.25
            
            # Set a disappear timer in frames.
            monster.disappear_timer = 3
            
    # Handle projectiles (spores in the case of mushrooms)
    # Projectiles point toward Maxine when they're spawned. (Spored?)
    projectiles_to_delete = set()
    for p in game.projectiles:
        p.animate()
        p.move_forward(p.speed)
        if game.maxine.collide_pixel(p):
            projectiles_to_delete.add(p)
            spore_count -= 1
            
            game.punish_maxine()

        # For a circular ring.
        #elif util.distance_points(p.center, CENTER) > RING_RADIUS:
        elif point_outside_signal_ring(p.center):
            # Delete projectiles that hit the ring
            projectiles_to_delete.add(p)
            spore_count -= 1
    
    for p in projectiles_to_delete:
        game.projectiles.remove(p)

    # Level 2, 4, 5 code
    # Process bouncing monsters
    if level in [2, 4, 5]:
        bm_speed = 5 * constants.SPEED
        bm_to_blow_up = set()
        for monster in game.bouncing_monsters:
            monster.animate()

            old_pos = monster.pos
            monster.move_forward(bm_speed)

            if point_outside_signal_ring(monster.pos):
                monster.pos = old_pos
                bounce_off_wall(monster)

            # Blow up the monster when it gets to the center and reward Maxine
            if game.cannon_in_level:
                if monster.collide_pixel(game.cannon):
                    bm_to_blow_up.add(monster)
                    game.reward_maxine()
            else:
                if util.distance_points(monster.center, constants.CENTER) < 45:
                   bm_to_blow_up.add(monster)
                   game.reward_maxine()

            # Punish Maxine if she collides with a bouncing monster
            if game.maxine.collide_pixel(monster):
                bm_to_blow_up.add(monster)
                game.punish_maxine()

        for monster in bm_to_blow_up:
            game.bouncing_monsters.remove(monster)
            game.dead_monsters.add(monster)
            monster.images = game.boom_images()
            monster.fps = 30
            monster.scale = 0.25
            
            # Set a disappear timer in frames.
            monster.disappear_timer = 31

    wm_to_blow_up = set()
    # Process spinning monsters that go to the other side
    for monster in game.walking_monsters:
        monster.animate()
    
        monster.x += monster.delta_x
        
        if point_outside_signal_ring(monster.pos):
            wm_to_blow_up.add(monster)
        
        # Punish Maxine if she collides with a walking monster
        if game.maxine.collide_pixel(monster):
            wm_to_blow_up.add(monster)
            game.punish_maxine()
    
    for monster in wm_to_blow_up:
        game.walking_monsters.remove(monster)
        game.dead_monsters.add(monster)
        monster.images = game.boom_images()
        monster.fps = 30
        monster.scale = 0.25
        
        # Set a disappear timer in frames.
        monster.disappear_timer = 31            

    # Level 5 Code
    # Get the gurk cannon to make a ring of spores and throw them at Maxine
    if level == 5:
        game.cannon_blast_timeout -= 1
        game.cannon.spore_timeout -= 5
        if game.cannon_blast_timeout >= 0:
            for spore in game.projectiles:
                spore.speed = 3
                ss = util.SpiralState(
                0.5, rotation, game.ring_height - 10, 1, constants.CENTER, game.ring_width / game.ring_height)
                ss.update()
                spore.angle = (ss.angle + 90) % 360
        else:
            if game.cannon_blast_timeout == -1:
                game.cannon_shooting = False
                for spore in game.projectiles:
                    spore.speed = 10
                    spore.point_towards(game.maxine)    
             
            if spore_count == 0:
                game.cannon_blast_timeout = game.cannon_blast_delay
                game.cannon_shooting = True

    # Level 6-8 code
    for monster in game.maze_monsters:
        monster.animate()
        monster.gridnav.update()
        monster.ai.update()
        monster.center = monster.gridnav.get_location()

    # Level 7-8 code (maze with a world map)
    if level in [7, 8]:
        for monster in game.maze_monsters:
            monster.gridnav.update()
            monster.ai.update()
            monster.map_x, monster.map_y = monster.gridnav.get_location()
            monster.center = lwm.convert_coords(monster.map_x, monster.map_y)
            monster.scale = 4 * monster.initial_scale * lwm.convert_scale(monster, images)

        for item in game.items:
            item.map_x, item.map_y = item.gridnav.get_location()
            item.center = lwm.convert_coords(item.map_x, item.map_y)
            item.scale = 1 / 8 * lwm.convert_scale(item, images)            

    # Level 6-8 code for collecting items
    if hasattr(game.maxine, 'gridnav'):
        items_collected = []
        for item in game.items:
            if game.maxine.gridnav.in_cell == item.gridnav.in_cell:
                # Only handle the sword for now
                if hasattr(item, 'weapon'):
                    items_collected.append(item)
                    game.maxine.fighter.equip_if_improvement(item.weapon)
                    
        for item in items_collected:
            game.items.remove(item)                

    # All levels code
    
    # Animate exploding monsters
    to_delete = set()
    for monster in game.dead_monsters:
        monster.animate()
        monster.disappear_timer -= 1

        if monster.disappear_timer <= 0:
            to_delete.add(monster)
            
    for monster in to_delete:
        game.dead_monsters.remove(monster)

    # Check if Maxine has won or lost (or is still going)
    if game_state == 'playing':
        if game.console_score >= 1000:
            game_state = 'lost'
        elif game.challenger_score >= 1000:
            finished_level()
            
    # Code for the transition between levels
    if game_state == 'won':
        if switch_level_timeout > 0:
            switch_level_timeout -=1
        else:
            start_next_level()
    
    # Make the mushroom boss vibrate at a different speed depending on RMS
    if game.cannon_in_level:
        game.cannon_dance()

def point_outside_signal_ring(point):
    '''Calculate if a position is colliding with the torus. From Math StackExchange.'''
    rx = game.torus_inner_width / 2
    ry = game.torus_inner_height / 2
    scaled_coords = (point[0] - constants.CENTER[0],
                     (point[1] - constants.CENTER[1]) * rx/ry)
    return np.linalg.norm(scaled_coords, 2) > rx

def on_key_down(key):
    global controls, serializer, playing_music, game

    # Switch between full screen and windowed
    if key == keys.F:
        set_fullscreen()
    elif key == keys.W:
        set_windowed()

    # Change graph type
    if key == keys.G:
        # Obsolete graph types
#        if graph_type == 'heatmap':
#            graph_type = 'scatterplot'
#        else:
#            graph_type = 'heatmap'

        if controls.corner_display == 'spike_graph':
            controls.corner_display = 'continuous_graph'
        else:
            controls.corner_display = 'spike_graph'
    
    # Turn music on and off
    if key == keys.M:
        playing_music = not playing_music
    
    # Temporary hack so you can test out levels more easily
    if key == keys.N:
        finished_level()
    
    # Save and load the state of the game to a file.
    if key == keys.S:
        # Only save the information that this player is in charge of updating
        if PLAYER == 'console':
            data = controls.save_to_dict()
            serializer.save_dict_to_file(data, 'console.json')
        else:
            data = game.save_arena_to_dict()
            serializer.save_dict_to_file(data, 'maxine.json')
    elif key == key.L:
        # Load the Maxine information only for the console player, because
        # the save information isn't complete enough to continue the game,
        # just enough to display one frame. But the console information is
        # enough to continue operating the console.
        if PLAYER == 'maxine':
            data = serializer.load_dict_from_file('console.json')
            controls.load_from_dict(data)

        if PLAYER == 'console':
            data = serializer.load_dict_from_file('maxine.json')
            game.load_arena_from_dict(data)

    # Move maxine around a grid (maze)
    if hasattr(game.maxine, 'gridnav'):
        game.maxine.gridnav.process_keypress(keyboard)

# Development tool: when the mouse is clicked, print the mouse coordinates in the window
def on_mouse_down(pos):
    print('Mouse clicked at:', pos)

# Temporary development tool: move a control around on the screen
def on_mouse_move(pos):
    global dev_control
    #dev_control = Actor('button_off')
    #dev_control.pos = pos
    #dev_control.scale = 0.5
    pass

# Prepare to move on to the next level
def finished_level():
    global game_state, level, switch_level_timeout
    global spore_count
    global game
    game_state = 'won'
    level += 1
    switch_level_timeout = 120
    # TODO send a signal to the server to close the file here and open a new file in start_next_level
    game.spiraling_monsters.clear()
    game.dead_monsters.clear()
    game.bouncing_monsters.clear()
    game.walking_monsters.clear()
    game.projectiles.clear()
    game.maze_monsters.clear()
    
    spore_count = 0
    game.cannon_in_level = False
    game.cannon_shooting = False 
    
    if hasattr(game.maxine, 'gridnav'):
        del game.maxine.gridnav
    
def start_next_level():
    global game_state
    global spore_count
    global level, maze, lwm
    global game
    game_state = 'playing'

    game.maxine_current_scale = 1
    game.maxine.pos = game_object.MAXINE_START
    game.maxine.scale = game_object.MAXINE_INITIAL_SCALE * game.maxine_current_scale

    game.challenger_score = 0
    game.console_score = 0

    game.draw_spirals = True

    # Zavier's levels
    if level in [3, 4, 5]:
        game.cannon_in_level = True
        game.cannon_shooting = True

    spore_count = 0

    # Dragon Tyrant level
    if level == 6:
        # Set up maze
        
        maze = mazes.PolarGrid(8)
        #mazes.RecursiveBacktracker.on(maze)
        mazes.GrowingTree.on(maze, mazes.GrowingTree.use_random)
        maze.braid()
        #maze.remove_walls(0.2)
        # This must be called after running the maze generation algorithm,
        # never before or it will block off the rooms half the time.
        maze.make_rooms()
        
        # Make Maxine small enough to fit in maze
        game.maxine.scale = 0.125

    # Logarithmic Map Level with a maze
    if level == 7:
        game.maxine.map_x = 0
        game.maxine.map_y = 0
        
        lwm = world_map.LogarithmicWorldMap(game, 1000)

        maze = mazes.PolarGrid(20, lwm)
        mazes.GrowingTree.on(maze, mazes.GrowingTree.use_random)
        maze.braid()
        maze.remove_walls(0.2)
        
    if level == 8:
        game.maxine.map_x = 0
        game.maxine.map_y = 0
        
        game.draw_panels = False
        game.set_torus_outer_size(WIDTH, HEIGHT)
        
        lwm = world_map.LogarithmicWorldMap(game, 3000)

        maze = mazes.PolarGrid(60, lwm)
        mazes.GrowingTree.on(maze, mazes.GrowingTree.use_random)
        maze.braid()
        maze.remove_walls(0.2)
        
        other_maxines = game.make_other_maxines()
        for m in other_maxines:
            m.gridnav = components.PolarGridNavigation(maze,
                maze.get_random_cell(), game, 15 // constants.SPEED)

    if level in [6, 7, 8]:
        game.draw_spirals = False
    
        # Give Maxine a Grid Navigation component
        game.maxine.gridnav = components.PolarGridNavigation(maze, maze[0, 0], game,
         15 // constants.SPEED)

        game.maxine.fighter = components.Fighter(1000, 1, 0)
        
        # Make a Shiny Sword
        sword = make_sword()
        game.items.add(sword)

    # This timer will have been shut down while the victory screen is displayed
    # so we need to start it up again
    if STANDALONE:
        delay = random.randrange(5, 8)
        clock.schedule_unique(add_cell, delay)

# Monster functions
# Level 1
def make_spore(shroom):
    '''Makes a spore starting at the center of the shroom and heading toward
    Maxine.'''
    spore = Actor('spore1')
    spore.images = ['spore1', 'spore2', 'spore3']
    spore.scale = 0.25
    spore.pos = shroom.pos
    spore.point_towards(game.maxine)
    spore.speed = 3 * constants.SPEED
    game.projectiles.add(spore)
    return spore

def get_spore_timeout():
    return random.randrange(60 * 2.5, 60 * 5)

def make_mushroom():
    mush = Actor('pink_oyster1')
    mush.images = ['pink_oyster1', 'pink_oyster2']
    mush.fps = 2
    mush.scale = 0.5
    
    # Set up the spiraling behavior with a component
    rotation = random.randrange(0, 360)
    mush.spiral_state = util.SpiralState(
        0.5, rotation, game.torus_inner_height, 1 * constants.SPEED, constants.CENTER, game.torus_inner_width / game.torus_inner_height)
    
    # Set the mushroom up to spawn a spore
    mush.spore_timeout = get_spore_timeout()
    
    return mush

# Level 2
def make_bouncer():
#    monster_type = random.choice(['monster1_right', 'monster2', 'monster3', 'monster4',
#        'monster5', 'monster6', 'monster7', 'monster8', 'monster9', 'monster10'])
    bouncer = Actor('purple_mushroom')
    bouncer.images = ['purple_mushroom']

    bouncer.fps = 1
    
    # Give it an initial position on the signal ring
    r = game.torus_inner_radius
    theta = random.randrange(0, 360)
    (x, y) = util.pol2cart(r, theta)
    coords = util.adjust_coords(x, y)

    bouncer.pos = coords
    
    bounce_off_wall(bouncer)
    
    return bouncer

# Levels 1-5
def make_spinner():
    spinner = Actor('spinshroom1')
    spinner.images = ['spinshroom'+str(i) for i in range(1, 9)]
    spinner.fps = 10
    spinner.scale = 0.2
    
    # Randomly start on the left or right side of the signal ring
    side = random.choice(['left', 'right'])
    
    r = game.torus_inner_radius
    theta = 0 if side == 'right' else 180
    (x, y) = util.pol2cart(r, theta)
    coords = util.adjust_coords(x, y)

    spinner.pos = coords

    speed = 3
    spinner.delta_x = -speed if side == 'right' else speed
    
    return spinner
    
def bounce_off_wall(monster):
    new_direction = random.randrange(0, 360)
    monster.angle = new_direction

# Level 3-5
def make_cannon_spore():
    '''Makes a spore starting at the center of the cannon and heading toward
    Maxine.'''
    if game.cannon_in_level:
        spore = Actor('spore1')
        spore.images = ['spore1', 'spore2', 'spore3']
        spore.scale = 0.25
        spore.pos = game.cannon.pos
        spore.point_towards(game.maxine)
        spore.speed = 3
        game.projectiles.add(spore)
        return spore

# Levels 6-8
def make_maze_monster(near_center = False):
    '''Makes a monster that moves around inside the maze. Randomly to start
    with.'''
    global maze
    
    monster_type = random.choice(['dragon', 'ghost', 'snake'])
    if monster_type == 'dragon':
        monster = Actor('dragon_tyrant_a')
        monster.images = ['dragon_tyrant_a']
        monster.initial_scale = 1 / 24
    elif monster_type == 'ghost':
        monster = Actor('ghost1')
        monster.images = ['ghost1', 'ghost2', 'ghost3']
        monster.fps = 2
        monster.initial_scale = 1 / 24
    elif monster_type == 'snake':
        monster = Actor('snalke1')
        monster.images = ['snalke1', 'snalke2']
        monster.fps = 2
        monster.initial_scale = 1 / 10

    # TODO don't spawn on top of another monster or Maxine
    if not near_center:
        loc = maze.get_random_cell()
    else:
        loc = maze.get_random_cell_near_cell(game.maxine.gridnav.in_cell, 8)
    monster.gridnav = components.PolarGridNavigation(maze, loc , game,
     60 // constants.SPEED)
    monster.ai = components.RandomMazeAI(monster.gridnav)
    monster.center = monster.gridnav.get_location()
    
    monster.fighter = components.Fighter(2, 1, 0)
    
    return monster

def make_sword():
    global maze, game
    
    sword = Actor('sword')
    sword.images = ['sword']
    sword.scale = 1 / 32

    # Use gridnav to give the sword a location in the maze. It doesn't move.
    sword.gridnav = components.PolarGridNavigation(maze, maze.get_random_cell(), game)
    sword.center = sword.gridnav.get_location()

    sword.weapon = components.ShinySword(game)

    return sword
    
# Neither of these next two functions work any more due to Jade removing obsolete
# code. They're just here for reference.
def make_midjourney_monster():
    cell_type = random.choice(['monster1_right', 'monster2', 'monster3', 'monster4',
        'monster5', 'monster6', 'monster7', 'monster8', 'monster9', 'monster10'])
    cell = Actor(cell_type)
    cell.sprite_name = cell_type
    return cell

def make_sars_monster():
    global animations

    cell_types = [('corn', 3), ('gurk', 2), ('icar', 3), ('lem', 19), ('olive', 4), ('sna', 3)]
    name, num_frames = random.choice(cell_types)
    animation = animated_image.AnimatedImage(name, num_frames)
    animations.add(animation)
    
    cell = Actor(name + '1')
    cell.animation = animation
    return cell

def add_cell():
    # This is called by the clock, not the update function (in standalone mode)
    global game_state
    if game_state != 'playing':
        return
        
    make_normal_monster = True
    # Sometimes add spinning mushrooms instead of the normal kind.
    if level in [1, 2, 3, 4, 5]:
        if random.randrange(0, 3) == 0:
            spinner = make_spinner()
            game.walking_monsters.add(spinner)
            make_normal_monster = False
    
    if make_normal_monster:
        if level in [1, 3]:
            mush = make_mushroom()
            game.spiraling_monsters.add(mush)
        elif level in [2, 4, 5]:
            bouncer = make_bouncer()
            game.bouncing_monsters.add(bouncer)
        elif level in [6, 7, 8]:
            monster = make_maze_monster(True)
            game.maze_monsters.add(monster)

    if STANDALONE:
        # Monsters come faster in Battle Royale
        if level == 8:
            delay = random.uniform(1, 2)
        else:
            delay = random.uniform(5, 8)
        clock.schedule_unique(add_cell, delay)

import parse_arguments
args = parse_arguments.parser.parse_args()
STANDALONE = not args.datadir and not args.live
LIVE = args.live
DATADIR = args.datadir
MULTIPLAYER = not args.player is None

if not args.player:
    PLAYER = 'maxine'
else:
    PLAYER = args.player # 'console'

BOARD = args.live # Could be None

if args.level:
    level = int(args.level)

# Detect Kent's computer and apply default parameters (can be overridden)
import platform
import sys
if platform.system() == 'Windows' and len(sys.argv) == 1:
    BOARD = 'Kent'
    LIVE = True
    PLAYER = 'console'
    STANDALONE = False
    DATADIR = None

TITLE = TITLE + f' ({PLAYER})'

if DATADIR:
    d = data.PrerecordedData(constants.NUM_BOXES)
    d.load_files(DATADIR)

elif STANDALONE:
    if PLAYER == 'maxine':
        clock.schedule_unique(add_cell, 4.0)   

elif LIVE:
    lilith_client.MAC = lilith_client.NAME2MAC[BOARD]
    lilith_client.setup()

    # Run the Lilith interaction loop in another thread
    t = threading.Thread(target=lilith_client.main)
    # Don't wait for this thread when the game exits
    t.setDaemon(True)
    t.start()
    
    d = data.LiveData(constants.NUM_BOXES)

if MULTIPLAYER and not LIVE:
    name = 'Kent'
    lilith_client.MAC = lilith_client.NAME2MAC[name]
    lilith_client.setup()

    print('Initializing lilith_client')
    # Run the Lilith interaction loop in another thread
    t = threading.Thread(target=lilith_client.main)
    # Don't wait for this thread when the game exits
    t.setDaemon(True)
    t.start()

serializer = serialization.Serializer()

#music.play('subgenie') 

pgzrun.go()

import sys; sys.exit(0)
