"""
LD31 o'clock
Entire Game On One Screen
"""

# System imports
import os

# Myrmidon imports
from myrmidon import Game, Entity
from myrmidon.consts import *


class Media(object):
    gfx = {}
    fnt = {}
    sfx = {}
    mus = {}
    def __init__(self):
        self.gfx['player'] = Game.load_image(os.path.join("gfx", "player.png"), sequence = True, width = 64, height = 64)
        self.gfx['grid'] = Game.load_image(os.path.join("gfx", "grid.png"), sequence = True, width = 128, height = 128)
        self.gfx['health'] = Game.load_image(os.path.join("gfx", "health.png"), sequence = True, width = 19, height = 18)
        self.gfx['medium_particle'] = Game.load_image(os.path.join("gfx", "medium_particle.png"))
        self.gfx['footstep1'] = Game.load_image(os.path.join("gfx", "footstep1.png"))
        self.gfx['footstep2'] = Game.load_image(os.path.join("gfx", "footstep2.png"))
        self.gfx['bump_particle'] = Game.load_image(os.path.join("gfx", "bump_particle.png"))
        self.gfx['shot'] = Game.load_image(os.path.join("gfx", "shot.png"))
        self.gfx['player_chunk'] = Game.load_image(os.path.join("gfx", "player_chunk.png"))
        self.gfx['background'] = Game.load_image(os.path.join("gfx", "background.png"))
        self.gfx['spawn_particle'] = Game.load_image(os.path.join("gfx", "spawn_particle.png"))
        self.gfx['shot_particle'] = Game.load_image(os.path.join("gfx", "shot_particle.png"))
        self.gfx['death_particle'] = Game.load_image(os.path.join("gfx", "death_particle.png"))
        self.fnt['fps'] = Game.load_font(os.path.join("fnt", "nulshock.ttf"), size = 40)
        self.fnt['timer'] = Game.load_font(os.path.join("fnt", "nulshock.ttf"), size = 40)
        self.fnt['final_score'] = Game.load_font(os.path.join("fnt", "nulshock.ttf"), size = 60)
        self.fnt['score_press_start'] = Game.load_font(os.path.join("fnt", "squared.ttf"), size = 40)
        self.fnt['title_name'] = Game.load_font(os.path.join("fnt", "squared.ttf"), size = 110)
        self.fnt['title_press_start'] = Game.load_font(os.path.join("fnt", "squared.ttf"), size = 40)
        self.fnt['player_select_press_buttons'] = Game.load_font(os.path.join("fnt", "squared.ttf"), size = 40)
        self.mus['title'] = Game.load_audio(os.path.join("music", "title.ogg"))
        self.mus['level'] = Game.load_audio(os.path.join("music", "level.ogg"))
        self.sfx['pressstart'] = Game.load_audio(os.path.join("sfx", "pressstart.wav"))
        self.sfx['playerregister'] = Game.load_audio(os.path.join("sfx", "playerregister.wav"))
        self.sfx['respawn'] = Game.load_audio(os.path.join("sfx", "respawn.wav"))
        self.sfx['bounce'] = Game.load_audio(os.path.join("sfx", "bounce.wav"))
        self.sfx['shoot'] = Game.load_audio(os.path.join("sfx", "shoot.wav"))
        self.sfx['death'] = Game.load_audio(os.path.join("sfx", "death.wav"))
        self.sfx['buildlevel'] = Game.load_audio(os.path.join("sfx", "buildlevel.wav"))
        self.sfx['timewarning'] = Game.load_audio(os.path.join("sfx", "timewarning.wav"))
        self.sfx['hurt'] = []
        for i in range(1,8):
            self.sfx['hurt'].append(Game.load_audio(os.path.join("sfx", "hurt" + str(i) + ".wav")))
