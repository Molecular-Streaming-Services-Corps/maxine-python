# A custom textbox class that works with PGZero.
# Based on https://stackoverflow.com/questions/46390231/how-can-i-create-a-text-input-box-with-pygame

import pygame as pg
import pgzero

COLOR_INACTIVE = pg.Color('lightskyblue3')
COLOR_ACTIVE = pg.Color('dodgerblue2')
FONT = pg.font.Font(None, 32)

class InputBox:

    def __init__(self, x, y, w, h, screen, keys, text=''):
        self.rect = pg.Rect(x, y, w, h)
        self.color = COLOR_INACTIVE
        self.text = text
        self.txt_surface = FONT.render(text, True, self.color)
        self.active = False
        self.entered_text = None
        self.screen = screen
        self.keys = keys

    def get_entered_text(self):
        et = self.entered_text
        self.entered_text = None
        return et

    def on_mouse_down(self, pos):
        # If the user clicked on the input_box rect.
        if self.rect.collidepoint(pos):
            # Toggle the active variable.
            self.active = not self.active
        else:
            self.active = False
        # Change the current color of the input box.
        self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE

    def on_key_down(self, key):
        if self.active:
            if key == self.keys.RETURN:
                self.entered_text = self.text
                self.text = ''
            elif key == self.keys.BACKSPACE:
                self.text = self.text[:-1]
            else:
                # Filter out letters and arrows
                if key.value >= ord('0') and key.value <= ord('9'):
                    c = chr(key.value)
                    self.text += c
            # Re-render the text.
            self.txt_surface = FONT.render(self.text, True, self.color)
        
    def update(self):
        # Resize the box if the text is too long.
        width = max(200, self.txt_surface.get_width()+10)
        self.rect.w = width

    def draw(self):
        # Blit the text.
        self.screen.blit(self.txt_surface, (self.rect.x+5, self.rect.y+5))
        # Blit the rect.
        pg.draw.rect(self.screen.surface, self.color, self.rect, 2)

input_boxes = []

