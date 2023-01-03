import random
import logging

# Set up logger for this module
logger = logging.getLogger('components')
logger.setLevel(logging.DEBUG)
import sys
handler = logging.StreamHandler(sys.stdout)
handler.formatter = logging.Formatter('%(asctime)s  %(name)s %(levelname)s: %(message)s')
logger.addHandler(handler)


class BaseComponent:
    pass

# Grid navigation components

class GridNavigation(BaseComponent):
    '''Keeps track of the position of the Actor in the maze.'''
    def __init__(self, grid, in_cell, game):
        self.grid = grid
        self.in_cell = in_cell
        self.game = game
        self.just_moved = False

class PolarGridNavigation(GridNavigation):
    '''Adds functions to navigate in a polar grid.'''
    def __init__(self, grid, in_cell, game, num_frames_for_move = 60):
        super().__init__(grid, in_cell, game)
        self.next_cell = None
        self.num_frames_for_move = num_frames_for_move
        self.num_frames_moved = 0
        self.sprite_direction = 'neutral'
        
    def move_inward(self):
        next_cell =  self.in_cell.inward
        if next_cell and self.in_cell.is_linked(next_cell):
            self.next_cell = next_cell
            
            bumped = self.bump(self.next_cell, True)
            # Don't move
            if bumped: self.next_cell = None
            for monster in bumped:
                self.game.hit_maze_monster(monster)
            
            # Change Maxine's sprite
            angle = self.grid.get_angle(self.in_cell)
            if angle < 45 or angle > 315:
                self.sprite_direction = 'down'
            elif angle >= 45 and angle < 135:
                self.sprite_direction = 'left'
            elif angle >= 135 and angle < 225:
                self.sprite_direction = 'up'
            else:
                self.sprite_direction = 'right'
    
    def move_ccw(self):
        next_cell = self.in_cell.ccw
        if next_cell and self.in_cell.is_linked(next_cell):
            self.next_cell = next_cell
            
            bumped = self.bump(self.next_cell, True)
            # Don't move
            if bumped: self.next_cell = None
            for monster in bumped:
                self.game.hit_maze_monster(monster)

            angle = self.grid.get_angle(self.in_cell)
            if angle < 45 or angle > 315:
                self.sprite_direction = 'left'
            elif angle >= 45 and angle < 135:
                self.sprite_direction = 'up'
            elif angle >= 135 and angle < 225:
                self.sprite_direction = 'right'
            else:
                self.sprite_direction = 'down'

    def move_cw(self):
        next_cell = self.in_cell.cw
        if next_cell and self.in_cell.is_linked(next_cell):
            self.next_cell = next_cell
            
            bumped = self.bump(self.next_cell, True)
            # Don't move
            if bumped: self.next_cell = None
            for monster in bumped:
                self.game.hit_maze_monster(monster)

            angle = self.grid.get_angle(self.in_cell)
            if angle < 45 or angle > 315:
                self.sprite_direction = 'right'
            elif angle >= 45 and angle < 135:
                self.sprite_direction = 'down'
            elif angle >= 135 and angle < 225:
                self.sprite_direction = 'left'
            else:
                self.sprite_direction = 'up'

    def move_outward(self, n):
        '''Moves to the nth outward neighbor. Every cell has at least the 0th outward neighbor
        (except edges). The middle cell has 6 outward neighbors. Some cells have 2 outward neighbors.'''
        outward = self.in_cell.outward
        if len(outward) > n  and self.in_cell.is_linked(outward[n]):
            self.next_cell = outward[n]
            
            bumped = self.bump(self.next_cell, True)
            # Don't move
            if bumped: self.next_cell = None
            for monster in bumped:
                self.game.hit_maze_monster(monster)
    
            angle = self.grid.get_angle(self.in_cell)
            if angle < 45 or angle > 315:
                self.sprite_direction = 'up'
            elif angle >= 45 and angle < 135:
                self.sprite_direction = 'right'
            elif angle >= 135 and angle < 225:
                self.sprite_direction = 'down'
            else:
                self.sprite_direction = 'left'
    
    def process_keypress(self, keyboard):
        '''Process a keypress by moving. Only relevant to Maxine.
        Uses the buttons 1-6 to move outward.'''
        if not self.finished_moving():
            logger.debug('Pressed a movement key while Maxine was still moving.') 
            return
        
        if keyboard.left:
            self.move_inward()
        elif keyboard.up:
            self.move_ccw()
        elif keyboard.down:
            self.move_cw()
        else:
            numbers_pressed = [keyboard.k_1, keyboard.k_2,
                keyboard.k_3, keyboard.k_4, keyboard.k_5, keyboard.k_6]
            
            for n, pressed in enumerate(numbers_pressed):
                if pressed:
                    self.move_outward(n)
                    break

    def get_location(self):
        if self.next_cell is None:
            return self.grid.get_center(self.in_cell)
        
        # New version
        proportion_moved = self.num_frames_moved / self.num_frames_for_move
        cn = self.grid.get_center(self.next_cell)
        ci = self.grid.get_center(self.in_cell)
        dx_complete = cn[0] - ci[0]
        dy_complete = cn[1] - ci[1]
        
        dx = dx_complete * proportion_moved
        dy = dy_complete * proportion_moved
        
        coords = (ci[0] + dx, ci[1] + dy)
        
        return coords

    def move_to_cell(self, cell):
        self.next_cell = cell
    
    def get_linked_cells(self):
        ret = []
        for c in self.in_cell.neighbors():
            if self.in_cell.is_linked(c):
                ret.append(c)
        return ret

    def finished_moving(self):
        return (self.next_cell is None or self.in_cell == self.next_cell)
    
    def update(self):
        if self.num_frames_moved == self.num_frames_for_move:
            self.sprite_direction = 'neutral'
        
            self.in_cell = self.next_cell
            self.next_cell = None
            self.num_frames_moved = 0
            
            self.just_moved = True
        elif self.next_cell is None:
            self.just_moved = False
            return
        else:
            # Move the character.
            self.num_frames_moved += 1
            
    def bump(self, cell, is_maxine = False):
        '''Detects any entities you would bump into if you moved to that cell.'''
        if is_maxine:
            entities = list(self.game.maze_monsters)
        else:
            entities = list(self.game.maze_monsters) + [self.game.maxine]
        bumped_entities = []
        for e in entities:
            if e.gridnav.in_cell is cell or e.gridnav.next_cell is cell:
                bumped_entities.append(e)
        
        if bumped_entities:
            logger.debug('object at cell %s tried to bump into: %s',
                repr(self.in_cell),
                [e.gridnav.in_cell for e in bumped_entities])
        
        return bumped_entities
    
# AI components

class BaseMazeAI(BaseComponent):
    def __init__(self, gridnav):
        self.gridnav = gridnav
        self.game = gridnav.game


class RandomMazeAI(BaseMazeAI):
    '''Takes a random step except it won't reverse its last
    step unless it's in a deadend. And it doesn't allow collisions.'''
    def __init__(self, gridnav):
        super().__init__(gridnav)
        self.prev_cell = gridnav.in_cell
        
    def move(self):
        options = self.gridnav.get_linked_cells()
        options = [c for c in options if not self.gridnav.bump(c)]
        # Prefer not to move back to the previous cell.
        best = [c for c in options if c is not self.prev_cell]
        # If we're in a dead end, go to the previous cell after all.
        # But stay still if all the linked cells are collisions.
        if not best:
            best = options
        
        if not best:
            return
        else:
            self.prev_cell = self.gridnav.in_cell
            cell = random.choice(best)
            self.gridnav.move_to_cell(cell)
    
    def update(self):
        if self.gridnav.finished_moving():
            self.move()

# Fighter, Inventory, Weapon and Item

class Fighter(BaseComponent):
    def __init__(self, max_hp, strength, defense):
        self.max_hp = max_hp
        self.hp = max_hp
        self.strength = strength
        self.defense = defense
        self.weapon = None
    
    def give_hit(self):
        hit = self.strength
        if self.weapon:
            hit += self.weapon.strength_bonus
        return hit
        
    def take_hit(self, damage):
        damage = damage - self.defense
        self.hp = max(0, self.hp - damage)
        
    def is_dead(self):
        return self.hp == 0
        
    def equip_if_improvement(self, weapon):
        if (self.weapon is None or
           weapon.strength_bonus > self.weapon.strength_bonus):
           
           self.weapon = weapon
        
class Item(BaseComponent):
    def __init__(self, name, game):
        self.name = name
        self.game = game
    
    def consume(self):
        raise NotImplementedError()

class HealingPotion(Item):
    def __init__(self, game):
        super().__init__('Healing potion', game)
    
    def consume(self):
        self.game.console_score = max(0, self.game.console_score - 100)

class Weapon(Item):
    def __init__(self, name, strength_bonus, game):
        super().__init__(name, game)
        self.strength_bonus = strength_bonus

class DullDagger(Weapon):
    def __init__(self, game):
        super().__init__('Dull dagger', 0, game)

class ShinySword(Weapon):
    def __init__(self, game):
        super().__init__('Shiny sword', 1, game)
        
class Inventory(BaseComponent):
    '''An inventory for the player (Maxine). This won't be used for now because
    it requires a complex on-screen menu to access.'''
    def __init__(self, game):
        self.game = game
        self.items = []
        self.size = 26
    
    def add_item(self, item):
        if len(self.items) < self.size:
            self.items.append(item)
            
    def remove_item(self, index):
        if index < len(self.items):
            del self.items[index]
