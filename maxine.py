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

#graph_type = 'heatmap'
graph_type = 'line_ring'
#graph_type = 'boxes_ring'

# This is required for the level with a gurk and rotating spores to work
DRAW_SPIRALS = True

game_state = 'playing' # becomes 'won' or 'lost'
level = 1
switch_level_timeout = 120
playing_music = True

'''Spike Graph'''
sg = None
'''Vertical Line Ring'''
vlr = None

# Temporary development tool
dev_control = None

spore_count = 0

maze = None

controls = None

challenger_image = Actor('challengeplayer')
challenger_image.center = (40, 40)

console_image = Actor('consoleplayer')
console_image.center = (40, 100)

# This is to call start_next_level in the first call to update() in case
# a level has been chosen on the command-line.
started_chosen_level = False

# Represents data from a stored file.
d = None

rotation = 0

def draw():
    global rotation, dev_control, sg, graph_type
    global challenger_image, console_image
    global game
    draw_living_background()

    screen.draw.text('CHALLENGER SCORE: ' + str(game.challenger_score), (90, 40))
    screen.draw.text('CONSOLE SCORE: ' + str(game.console_score), (90, 100))

    #Draw Player Images   
    challenger_image.draw()    
    console_image.draw()

    # Draw the microscope video in front of the background and behind the signal ring
    video_ops.draw_video(screen)
    
    graphs.draw_torus(screen, images)
    
    if graph_type == 'line_ring':
        vlr.draw()
    else:
        graphs.draw_graph(i, d, graph_type, screen, STANDALONE)
    
    if sg:
        sg.draw()
    
    # Dragon Tyrant level
    if level == 6 and maze:
        maze.draw(screen)
    
    # Now we draw the controls for both players.
    controls.draw()
    
    if dev_control:
        dev_control.draw()

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
    for monster in game.dead_monsters:
        monster.draw()
    for monster in game.maze_monsters:
        monster.draw()
        
    for p in game.projectiles:
        p.draw()

    # Draw the signal ring.
    RED = (200, 0, 0)
    ring_rect = Rect((constants.CENTER[0] - constants.RING_WIDTH / 2, constants.CENTER[1] - constants.RING_HEIGHT / 2), 
                     (constants.RING_WIDTH, constants.RING_HEIGHT))
    pygame.draw.ellipse(screen.surface, RED, ring_rect, width = 1)
    
    if DRAW_SPIRALS:
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
    GAP = 0.5
    MAX_THETA = constants.TORUS_INNER_HEIGHT
    STEP_DEGREES = 10
    
    for theta in range(0, MAX_THETA, STEP_DEGREES):
        (x, y) = util.spiral(GAP, rotation, theta)
        (x, y) = util.adjust_coords(x, y)
        screen.draw.filled_circle((x, y), 1, color)

step_count = 0
space_pressed_before = False
button_pressed_before = False
def update():
    global i, step_count, d, space_pressed_before, button_pressed_before
    global logger
    global playing_music
    global sg
    global vlr
    global started_chosen_level
    global controls
    step_count += 1
    if step_count % 10 == 0:
        i += 1
        #print('update(): i:', i)

    if keyboard.q:
        import sys; sys.exit(0)
    
    if not started_chosen_level:
        start_next_level()
        started_chosen_level = True
    
    # Update the microscope video
    video_ops.update_video()

    if not sg:
        sg = graphs.SpikeGraph(screen, Rect)
    
    if not vlr:
        vlr = graphs.VerticalLineRing(screen)
    
    if not controls:
        controls = controls_object.Controls(Actor, serializer, LIVE, PLAYER, screen)
    
    # Advance the datafile and make a monster appear on a spike.
    # If we're in STANDALONE mode, a timer will make the monster appear.
    if DATADIR:
        d.get_one_frame_current()

        frame = d.get_frame()
                
        last_n_samples = d.get_last_n_samples(1667*constants.NUM_BOXES)
        vlr.give_samples(last_n_samples)

        maxes_mins = data.Data.calculate_maxes_and_mins(last_n_samples)
        spike_exists = data.Data.end_spike_exists(maxes_mins)
        if spike_exists:
            sg.set_frame(frame)
            vlr.add_spike()

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
        #d.try_to_catch_up()
        lilith_client.request_data(lilith_client.ws, 1)
    
        spikes = d.load_received_samples_and_count_spikes()
    
        frame = d.get_frame()
        if playing_music and not data is None:
            music_ops.current_to_frequency(frame)    
            music_ops.current_to_volume(frame)
        
        if spikes > 0:
            sg.set_frame(frame)
    
        if PLAYER == 'maxine':
            for i in range(0, spikes * MONSTERS_PER_SPIKE):
                add_cell() 
                
        last_n_samples = d.get_last_n_frames(constants.NUM_BOXES)
        vlr.give_samples(last_n_samples)
        
        booleans = d.get_recent_frames_contain_spikes()
        for b in booleans:
            vlr.advance_n_frames(1)
            if b:
                vlr.add_spike()
        
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
            logger.info('loaded controls state from the internet')
        elif ty == 'maxine' and PLAYER == 'console':
            game.load_arena_from_dict(wrapper)
            logger.info('loaded arena state from the internet')

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
    s = 6
    
    if game.maxine.alive and level != 6:
        prev_pos = game.maxine.pos

        # Allow the user to use either the keyboard or the joystick    
        if keyboard.left:
            game.maxine.left -= s
        elif keyboard.right:
            game.maxine.left += s
        if keyboard.up:
            game.maxine.top -= s
        elif keyboard.down:
            game.maxine.bottom += s
            
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
        if level != 6:
            if (game.maxine.collide_pixel(game.pore) or 
                (game.cannon_in_level and game.maxine.collide_pixel(game.cannon))):
                game.kill_maxine()
        
        if point_outside_signal_ring(game.maxine.center):
            game.maxine.pos = prev_pos

    # Update Maxine's position onscreen after she moves on the maze.
    if level == 6:
        # This is necessary because of the moment that the level is 6 but it hasn't been initialized yet.
        if hasattr(game.maxine, 'gridnav'):
            game.maxine.gridnav.update()
            game.maxine.center = game.maxine.gridnav.get_location()

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
        bm_speed = 5
        bm_to_blow_up = set()
        for monster in game.bouncing_monsters:
            monster.animate()

            old_pos = monster.pos
            monster.move_forward(bm_speed)

            if point_outside_signal_ring(monster.pos):
                monster.pos = old_pos
                bounce_off_wall(monster)

            # Blow up the monster when it gets to the center and reward Maxine
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

    # Level 5 Code
    # Get the gurk cannon to make a ring of spores and throw them at Maxine
    if level == 5:
        game.cannon_blast_timeout -= 1
        game.cannon.spore_timeout -= 5
        if game.cannon_blast_timeout >= 0:
            for spore in game.projectiles:
                spore.speed = 3
                ss = util.SpiralState(
                0.5, rotation, constants.RING_HEIGHT - 10, 1, constants.CENTER, constants.RING_WIDTH / constants.RING_HEIGHT)
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

    # Level 6 code
    for monster in game.maze_monsters:
        monster.gridnav.update()
        monster.ai.update()
        monster.center = monster.gridnav.get_location()

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

def point_outside_signal_ring(point):
    '''Calculate if a position is colliding with the torus. From Math StackExchange.'''
    rx = constants.TORUS_INNER_WIDTH / 2
    ry = constants.TORUS_INNER_HEIGHT / 2
    scaled_coords = (point[0] - constants.CENTER[0],
                     (point[1] - constants.CENTER[1]) * rx/ry)
    return np.linalg.norm(scaled_coords, 2) > rx

def on_key_down(key):
    global graph_type, controls, serializer, playing_music, game

    # Switch between full screen and windowed
    if key == keys.F:
        set_fullscreen()
    elif key == keys.W:
        set_windowed()

    # Change graph type
    if key == keys.G:
        if graph_type == 'heatmap':
            graph_type = 'scatterplot'
        else:
            graph_type = 'heatmap'
    
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
    game.projectiles.clear()
    game.maze_monsters.clear()
    
    spore_count = 0
    game.cannon_in_level = False
    game.cannon_shooting = False 
    
    if hasattr(game.maxine, 'gridnav'):
        del maxine.gridnav
    
def start_next_level():
    global game_state
    global spore_count
    global level, maze
    global game
    game_state = 'playing'

    game.maxine_current_scale = 1
    game.maxine.pos = game_object.MAXINE_START
    game.maxine.scale = game_object.MAXINE_INITIAL_SCALE * game.maxine_current_scale

    game.challenger_score = 0
    game.console_score = 0

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
        
        # Give Maxine a Grid Navigation component
        game.maxine.gridnav = components.PolarGridNavigation(maze, maze[0, 0], game)

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
    spore = Actor('spore')
    spore.images = ['spore1', 'spore2', 'spore3']
    spore.scale = 0.25
    spore.pos = shroom.pos
    spore.point_towards(game.maxine)
    spore.speed = 3
    game.projectiles.add(spore)
    return spore

def get_spore_timeout():
    return random.randrange(60 * 2.5, 60 * 5)

def make_mushroom():
    mush = Actor('mushdance1')
    mush.images = ['mushdance1', 'mushdance2', 'mushdance3']
    mush.fps = 3
    mush.scale = 0.5
    
    # Set up the spiraling behavior with a component
    rotation = random.randrange(0, 360)
    mush.spiral_state = util.SpiralState(
        0.5, rotation, constants.TORUS_INNER_HEIGHT, 1, constants.CENTER, constants.TORUS_INNER_WIDTH / constants.TORUS_INNER_HEIGHT)
    
    # Set the mushroom up to spawn a spore
    mush.spore_timeout = get_spore_timeout()
    
    return mush

# Level 2
def make_bouncer():
    monster_type = random.choice(['monster1_right', 'monster2', 'monster3', 'monster4',
        'monster5', 'monster6', 'monster7', 'monster8', 'monster9', 'monster10'])
    bouncer = Actor(monster_type)
    bouncer.images = [monster_type]
    bouncer.fps = 1
    
    # Give it an initial position on the signal ring
    r = constants.TORUS_INNER_RADIUS
    theta = random.randrange(0, 360)
    (x, y) = util.pol2cart(r, theta)
    coords = util.adjust_coords(x, y)

    bouncer.pos = coords
    
    bounce_off_wall(bouncer)
    
    return bouncer

def bounce_off_wall(monster):
    new_direction = random.randrange(0, 360)
    monster.angle = new_direction

# Level 3-5
def make_cannon_spore():
    '''Makes a spore starting at the center of the cannon and heading toward
    Maxine.'''
    if game.cannon_in_level:
        spore = Actor('spore')
        spore.images = ['spore1', 'spore2', 'spore3']
        spore.scale = 0.25
        spore.pos = game.cannon.pos
        spore.point_towards(game.maxine)
        spore.speed = 3
        game.projectiles.add(spore)
        return spore

# Level 6
def make_dragon():
    '''Makes a dragon that moves around inside the maze. Randomly to start
    with.'''
    global maze
    
    dragon = Actor('dragon_tyrant_a')
    dragon.images = ['dragon_tyrant_a']
    dragon.scale = 1 / 32
    # TODO don't spawn on top of another dragon or Maxine
    dragon.gridnav = components.PolarGridNavigation(maze, maze.get_random_cell(), game)
    dragon.ai = components.RandomMazeAI(dragon.gridnav)
    dragon.center = dragon.gridnav.get_location()
    
    return dragon

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
        
    if level in [1, 3]:
        mush = make_mushroom()
        game.spiraling_monsters.add(mush)
    elif level in [2, 4, 5]:
        bouncer = make_bouncer()
        game.bouncing_monsters.add(bouncer)
    elif level == 6:
        dragon = make_dragon()
        game.maze_monsters.add(dragon)

    if STANDALONE:
        delay = random.randrange(5, 8)
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
