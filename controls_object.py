import pygame

import colors
import lilith_client
import constants
import time

class Controls:
    def __init__(self, Actor, serializer, LIVE, PLAYER, screen):
        self.LIVE = LIVE
        self.PLAYER = PLAYER
        self.screen = screen
    
        # Pink panel in the bottom right
        self.panel = Actor('panel')
        self.panel.right = constants.WIDTH
        self.panel.bottom = constants.HEIGHT
    
        # LCD font
        pygame.font.init()
        self.font = pygame.font.Font('ds-digi.ttf', 40)
        
        self.voltage_knob = Actor('voltage_knob')
        #self.voltage_knob.left = 10
        #self.voltage_knob.top = 10
        self.voltage_knob.pos = (1596, 527)

        #self.bg = Actor('led_display')
        #self.bg.left = 10
        ## voltage_knob.png is 83x83 and the voltage knob is drawn at 10,10
        #self.bg.top = 10 + 83 + 10

        self.zap_lever = Actor('switch_big_frame_1')
        self.zap_lever.images = ['switch_big_frame_1']
        #self.zap_lever.left = 10
        #self.zap_lever.top = 10
        self.zap_lever.pos = (1730, 579)
        
        self.zap_timeout = 0
        
        self.syringe_value = 0

        self.syringemeter = Actor('totallytubular')
        self.syringemeter.left = 1300
        self.syringemeter.top = 830

        
        # This is an index into a list of speed settings. Can be negative.
        self.pump_speed_index = 0
        self.pump_speed_delays = [20, 10, 5, 2, 1]
        
        self.hydrowag_switch = Actor('switch_green_off')
        self.hydrowag_switch.images = ['switch_green_off']
        self.hydrowag_switch.pos = (1731, 665)
        self.hydrowag_on = False
        self.hydrowag_moving_forward = True
        self.hydrowag_timeout = 0
        
        self.sawtooth_switch = Actor('switch_blue_off')
        self.sawtooth_switch.images = ['switch_blue_off']
        self.sawtooth_switch.pos = (1731, 719)
        self.sawtooth_on = False
        self.sawtooth_frame = 0

        self.potion_holder = PotionHolder(Actor, serializer, LIVE)

        self.drop_button = Actor('button_off')
        self.drop_button.images = ['button_off']
        self.drop_button.pos = (1483, 707)
        self.button_timeout = 0
        
        self.controls = [self.voltage_knob, self.zap_lever, self.syringemeter,
                         self.hydrowag_switch, self.sawtooth_switch,
                         self.potion_holder, self.drop_button]
        # The index of the presently selected control
        self.control_index = 0
        self.voltage_index = 0
        self.zap_index = 1
        self.syringe_index = 2
        self.hydrowag_index = 3
        self.sawtooth_index = 4
        self.potion_index = 5
        self.drop_index = 6
        
        self.old_voltage = 0
        self.voltage = 0
        self.old_angle = 0
          
    def update(self):
        # Zapper stuff
        if self.PLAYER == 'console':
            if self.zap_timeout > 0:
                self.zap_timeout -= 1    

        # This code runs on both maxine and console, so maxine can draw the lever correctly
        # when the timeout is updated over the internet
        if self.zap_timeout > 0:
            self.zap_lever.images = ['switch_big_frame_2']
        else:
            self.zap_lever.images = ['switch_big_frame_1']
            
            if self.voltage != self.old_voltage:
                self.set_voltage(self.old_voltage)
            self.voltage_knob.angle = self.old_angle
        
        self.zap_lever.animate()

        # Hydrowag stuff
        if self.hydrowag_on:
            self.hydrowag_switch.images = ['switch_green_on']
        else:
            self.hydrowag_switch.images = ['switch_green_off']
        
        self.hydrowag_switch.animate()
        
        # Move the pump back and forward fast
        if self.hydrowag_on and self.PLAYER == 'console' and self.LIVE:
            if self.hydrowag_timeout > 0:
                self.hydrowag_timeout -= 1
                
                if self.hydrowag_moving_forward:
                    lilith_client.move_pump(500, 1)
                else:
                    lilith_client.move_pump(-500, 1)
            else:
                self.hydrowag_moving_forward = not self.hydrowag_moving_forward
                self.hydrowag_timeout = 60

        # Sawtooth stuff
        if self.sawtooth_on:
            self.sawtooth_switch.images = ['switch_blue_on']
        else:
            self.sawtooth_switch.images = ['switch_blue_off']
        
        self.sawtooth_switch.animate()

        if self.sawtooth_on and self.PLAYER == 'console' and self.LIVE:
            if self.sawtooth_frame == 180:
                self.sawtooth_frame = 0
            else:
                self.sawtooth_frame += 1
            
            MIN_VOLTAGE = -1000
            MAX_VOLTAGE = 1000
            RANGE = MAX_VOLTAGE - MIN_VOLTAGE
            voltage = int(RANGE * self.sawtooth_frame / 180 + MIN_VOLTAGE)
            self.set_voltage(voltage)

            # Only change the angle while sawtooth is on
            v = self.find_angle_from_voltage(self.voltage)
            if v:
                self.voltage_knob.angle = v

        # Hack: continuously rotate the voltage knob to test the display
        #self.voltage_knob.angle = int((self.voltage_knob.angle - 1) % 360)
        
        # Move the pump if required (controlled by the syringe)
        if self.LIVE and self.PLAYER == 'console':
            #logger.debug('pump_speed_index: %s', self.pump_speed_index)
            if self.pump_speed_index == 0:
                # Override the current number of steps and stop the pump
                lilith_client.move_pump(0, 0)
            elif self.pump_speed_index > 0:
                idx = self.pump_speed_index - 1
                lilith_client.move_pump(500, self.pump_speed_delays[idx])
            else:
                idx = abs(self.pump_speed_index) - 1
                lilith_client.move_pump(-500, self.pump_speed_delays[idx])
        
        self.potion_holder.update()

        # Stuff for the drop-adding button        
        if self.button_timeout == 0:
            self.drop_button.images = ['button_off']
        else:
            self.drop_button.images = ['button_on']
            self.button_timeout -= 1

        self.drop_button.animate()

    def draw_text(self, text, coords):
        surface = self.font.render(text, False, colors.RED)
        self.screen.blit(surface, coords)

    def draw(self):
        self.panel.draw()
    
        # Set the control that's presently selected to be a bit bigger.
        for control in self.controls:
            control.scale = 1
        self.controls[self.control_index].scale = 1.2
        self.drop_button.scale *= 0.5
     
        self.voltage_knob.draw()
        
        #self.bg.draw()
        
        #self.draw_text(str(self.voltage) + ' MV', (self.bg.left + 15, self.bg.top + 2))
        self.draw_text(str(self.voltage) + ' MV', (1545, 594))

        self.zap_lever.draw()
        
        #self.syringe.draw()
        
        self.hydrowag_switch.draw()
        
        self.sawtooth_switch.draw()

        self.potion_holder.draw()
        
        self.drop_button.draw()
        
        # Draw the number of drops added
        ph = self.potion_holder
        drops = ph.get_drops()
        self.draw_text(str(drops), (1470, 770))
        
        self.syringemeter.draw()

    def select_down(self):
        '''Select the control below the present one. Wraps around.'''
        self.control_index = (self.control_index + 1) % len(self.controls)

    def select_up(self):
        '''Select the control above the present one. Wraps around.'''
        self.control_index = (self.control_index - 1) % len(self.controls)

    def push(self):
        if self.control_index == self.zap_index:
            # 100 milliseconds in frames
            self.zap_timeout = 6
            
            # Send a message to change the voltage
            self.set_voltage(1000)
        elif self.control_index == self.hydrowag_index:
            self.hydrowag_on = not self.hydrowag_on
            # hydrowag has just been turned on now
            if self.hydrowag_on:
                self.hydrowag_moving_forward = True
                self.hydrowag_timeout = 60
        elif self.control_index == self.sawtooth_index:
            self.sawtooth_on = not self.sawtooth_on
            if self.sawtooth_on:
                self.old_voltage = self.voltage
                self.old_angle = self.voltage_knob.angle
            else:
                self.set_voltage(self.old_voltage)
                self.voltage_knob.angle = self.old_angle
        elif self.control_index == self.drop_index:
            # Only respond when the button is up
            if self.button_timeout == 0:
                self.potion_holder.on_button_pushed()
        
            self.button_timeout = 6
        
    def push_left(self):
        if self.control_index == self.voltage_index:
            if self.voltage_knob.angle != 170: # +17 * 10
                self.voltage_knob.angle = (self.voltage_knob.angle + 17) % 360

            voltage = self.find_voltage_from_angle(self.voltage_knob.angle)
            self.set_voltage(voltage)
            self.old_voltage = voltage
            self.old_angle = self.voltage_knob.angle
        elif self.control_index == self.syringe_index:
            self.pump_speed_index = min(len(self.pump_speed_delays), 
                                        self.pump_speed_index + 1)
        elif self.control_index == self.potion_index:
            self.potion_holder.push_left()
        
    def push_right(self):
        if self.control_index == self.voltage_index:
            if self.voltage_knob.angle != 190: # -17 * 10
                self.voltage_knob.angle = (self.voltage_knob.angle - 17) % 360
            
            voltage = self.find_voltage_from_angle(self.voltage_knob.angle)
            self.set_voltage(voltage)
            self.old_voltage = voltage
            self.old_angle = self.voltage_knob.angle
        elif self.control_index == self.syringe_index:
            self.pump_speed_index = max(-len(self.pump_speed_delays), 
                                        self.pump_speed_index - 1)
        elif self.control_index == self.potion_index:
            self.potion_holder.push_right()

    def find_voltage_from_angle(self, angle):
        if angle in [360, 0]:
            voltage = 0
        elif angle > 0 and angle <= 170:
            # Negative voltage
            voltage = int(-1 * angle / 17 * 100)
        else:
            # Positive voltage
            angle_compliment = (360 - angle) % 360
            voltage = int(angle_compliment / 17 * 100)

        return voltage

    def find_angle_from_voltage(self, voltage):
        if voltage > 1000 or voltage < -1000:
            angle = 190
        elif voltage == 0:
            angle = 0
        elif voltage > 0:
            angle = int(360 - voltage / 100 * 17)
        else:
            # Negative voltage
            angle = int(-voltage / 100 * 17)
        
        return angle

    def set_voltage(self, voltage):
        if self.LIVE and self.PLAYER == 'console':
            lilith_client.set_bias(voltage)
        self.voltage = voltage

    def save_to_dict(self):
        save = {}
        wrapper = {'type': 'controls', 'state': save}
        
        save['control_index'] = self.control_index
        save['voltage_knob_angle'] = self.voltage_knob.angle
        save['voltage'] = self.voltage
        save['old_voltage'] = self.old_voltage
        save['zap_timeout'] = self.zap_timeout
        save['hydrowag_on'] = self.hydrowag_on
        save['sawtooth_on'] = self.sawtooth_on
        
        ph = self.potion_holder
        save['potion_selected'] = ph.selected
        save['drops_readout'] = ph.get_drops()
        
        save['button_timeout'] = self.button_timeout
        
        return wrapper
        
    def load_from_dict(self, wrapper):
        assert(wrapper['type'] == 'controls')
        save = wrapper['state']
        
        self.control_index = save['control_index']
        self.voltage_knob.angle = save['voltage_knob_angle']
        self.voltage = save['voltage']
        self.old_voltage = save['old_voltage']
        
        # Let the update function move the control except when the lever is first pressed
        zt = save['zap_timeout']
        if zt == 6:
            self.zap_timeout = zt
        
        self.hydrowag_on = save['hydrowag_on']
        self.sawtooth_on = save['sawtooth_on']
        self.potion_holder.selected = save['potion_selected']
        self.potion_holder.num_drops[self.potion_holder.selected] = save['drops_readout']
        
        bt = save['button_timeout']
        if bt == 6:
            self.button_timeout = bt

class PotionHolder:
    def __init__(self, Actor, serializer, LIVE):
        self.serializer = serializer
        self.LIVE = LIVE
    
        self.holder = Actor('potion_holder')
        self.holder.pos = (1600, 730)
    
        self.selected = 0
        self.potions = [None] * 4
        self.actors = [Actor(f'potion_{n}') for n in range(1, 4 + 1)] 
        self.scale = 1
    
        self.num_drops = [0, 0, 0, 0]
        # This list contains (list not tuple) pairs of
        # [timestamp, potion index] for when a potion was dropped
        self.drop_history = []

    def update(self):
        self.set_indexes()
        
    def set_indexes(self):
        self.potions[(0 - self.selected) % 4] = self.actors[0]
        self.potions[(1 - self.selected) % 4] = self.actors[1]
        self.potions[(2 - self.selected) % 4] = self.actors[2]
        self.potions[(3 - self.selected) % 4] = self.actors[3]
        
        self.holder.scale = self.scale
        # Draw the top potion bigger
        for i in range(0, 4):
            self.potions[i].scale = 0.5 * self.scale
        self.potions[0].scale = 0.7 * self.scale
        
        # Move them all to the correct position
        self.potions[0].pos = (1602, 680)
        self.potions[1].pos = (1654, 726)
        self.potions[2].pos = (1611, 788)
        self.potions[3].pos = (1556, 739)
    
    def draw(self):
        self.holder.draw()
        
        for potion in self.potions:
            potion.draw()

    def push_left(self):
        self.selected = (self.selected + 1) % 4

    def push_right(self):
        self.selected = (self.selected - 1) % 4

    def on_button_pushed(self):
        self.num_drops[self.selected] += 1
        
        update = [time.time(), self.selected]
        self.drop_history.append(update)

        if self.LIVE:
            data = self.num_drops
            json_string = self.serializer.save_dict_to_string(data)
            lilith_client.set_metadata('drop_counts', json_string)
            
            data = self.drop_history
            json_string =  self.serializer.save_dict_to_string(data)
            lilith_client.set_metadata('drop_history', json_string)
    
            # Check if it worked
            lilith_client.get_metadata('drop_counts', lilith_client.ws)
            lilith_client.get_metadata('drop_history', lilith_client.ws)
            
    def get_drops(self):
        return self.num_drops[self.selected]

