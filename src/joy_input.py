"""
LD31 o'clock
Entire Game On One Screen
"""

# System imports
import sys
import pygame

# Myrmidon imports
from myrmidon import Game, Entity
from myrmidon.consts import *

class JoyInput(Entity):
    joys = []    
    def execute(self, window):
        self.window = window        
        pygame.joystick.init()
        for i in range(pygame.joystick.get_count()):
            self.joys.append(Joystick(i))
        while True:
            for joy in self.joys:
                joy.update()
            yield


class Joystick(object):
    axes = []
    buttons = []
    released_buttons = []
    def __init__(self, id):
        self.id = id
        self.obj = pygame.joystick.Joystick(id)
        self.obj.init()
        self.axes = [0.0] * self.obj.get_numaxes()
        self.buttons = [0] * self.obj.get_numbuttons()
        self.released_buttons = [0] * self.obj.get_numbuttons()

    def update(self):
        for i in range(len(self.axes)):
            self.axes[i] = self.obj.get_axis(i)
        for i in range(len(self.buttons)):
            b = self.obj.get_button(i)
            if not b and self.buttons[i]:
                self.released_buttons[i] = True
            else:
                self.released_buttons[i] = False
            self.buttons[i] = b            
        
