"""
LD31 o'clock
Entire Game On One Screen
"""
# Fix on python 2
from __future__ import (
unicode_literals,
print_function,
division,
absolute_import,
)

from ctypes import util
try:
    from OpenGL.platform import win32
except AttributeError:
    pass

# System imports
import sys
import math
import random
import copy

# Myrmidon imports
from myrmidon import Game, Entity
from myrmidon.consts import *

# Game imports
from mrf.mathutil import Vector2d
from media import Media
from joy_input import JoyInput
from particles import ParticleSystem

if sys.platform == 'win32':
    sys.path += ['.']

class Window(Entity):
    """Primary core Entity"""
    DEBUG = False

    particle_emitters = {}
    max_players = 4
    num_players = 4
    timer_length = 90
    timer_last_section = 30
    cam_shake = [0, 0]
    all_tiles_claimed = False
    playing = False
    timer = None
    score_board = None
    title = None
    player_select = None
    selected_players = []

    STATE_TITLE = 1
    STATE_SELECT_PLAYERS = 2
    STATE_PLAYING = 3
    STATE_SCORES = 4

    def execute(self):
        import pygame.mixer
        pygame.mixer.set_num_channels(32)
        self.media = Media()
        if self.DEBUG:
            self.fps_text = Game.write_text(0.0, 0.0, font = self.media.fnt['fps'], text = 0)
        self.input = JoyInput(self)
        self.setup_particle_system()
        self.background = Background(self)
        self.state = None
        self.grid = None
        self.change_state(Window.STATE_TITLE)
        while True:
            ######
            ## TITLE
            ######
            if self.state == Window.STATE_TITLE:
                if self.title is None:
                    self.title = Title(self)
                # Escape to quit
                if Game.keyboard_key_released(K_ESCAPE):
                    sys.exit()
            ######
            ## PLAYER SELECT
            ######
            if self.state == Window.STATE_SELECT_PLAYERS:
                if self.player_select is None:
                    self.player_select = PlayerSelect(self)
                # Escape to quit
                if Game.keyboard_key_released(K_ESCAPE):
                    sys.exit()
            ######
            ## PLAYING
            ######
            if self.state == Window.STATE_PLAYING:
                if self.grid is None:
                    self.grid = Grid(self)
                    for x in range(30):
                        yield
                    self.grid.init()
                    self.media.mus['level'].sound.set_volume(.7)
                    self.media.mus['level'].sound.play(loops = -1)
                if self.playing:
                    # Second timer phase
                    if self.timer is None:
                        self.timer = Timer(self)
                    if Game.keyboard_key_released(K_F11) and self.DEBUG:
                        if not self.timer is None:
                            self.timer.time = 3
                        self.all_tiles_claimed = True
                    # Leave playing
                    if Game.keyboard_key_released(K_ESCAPE):
                        self.end_timer()
            ######
            ## SCORES
            ######
            if self.state == Window.STATE_SCORES:
                if self.score_board is None:
                    self.grid = None
                    self.score_board = ScoreBoard(self)
                # Escape to quit
                if Game.keyboard_key_released(K_ESCAPE):
                    sys.exit()
            # Cam shake
            for i in range(2):
                self.cam_shake[i] *= .9
            # FPS text
            if self.DEBUG:
                self.fps_text.text = str(Game.current_fps)
            yield

    def change_state(self, state):
        self.state = state

    def do_cam_shake(self, amount):
        self.cam_shake[0] += random.randint(-amount, amount)
        self.cam_shake[1] += random.randint(-amount, amount)
        for i in range(2):
            if self.cam_shake[i] > 50:
                self.cam_shake[i] = 10

    def start_game(self):
        self.title = None
        self.player_select = None
        self.score_board = None
        self.all_tiles_claimed = False
        self.playing = True
        self.players = {}
        for p_id in self.selected_players:
            self.players[p_id] = Player(self, p_id)

    def end_timer(self):
        self.playing = False
        if not self.timer is None:
            self.timer.time = 0
        self.timer = None
        self.do_cam_shake(100)
        for p_id in self.players:
            self.players[p_id].die()
        self.media.mus['level'].sound.fadeout(2000)
        self.media.sfx['timewarning'].sound.stop()
        self.media.sfx['buildlevel'].sound.play()
        self.count_up_scores()
        self.grid.die()

    def count_up_scores(self):
        self.player_scores = {}
        for p_id in self.players:
            self.player_scores[p_id] = 0
        for tile in self.grid.tiles:
            if tile.claimed:
                self.player_scores[tile.claimed_by] += 1

    def respawn_player(self, player_num):
        self.players[player_num] = Player(self, player_num, respawn = True)

    def grid_pos_to_screen(self, x, y):
        return (self.grid.origin_screen_pos[0] + (x * (GridTile.tile_width * .75)),
                self.grid.origin_screen_pos[1] + (y * (GridTile.tile_height)))

    def screen_to_grid_pos(self, x, y):
        if not self.grid:
            return(0, 0)
        x = x - self.grid.origin_screen_pos[0] - (GridTile.tile_width / 2)
        _x = math.ceil(x / (GridTile.tile_width * .75))
        y = y - self.grid.origin_screen_pos[1] - (GridTile.tile_height / 2)
        if _x % 2:
            y += GridTile.tile_height / 2
        _y = math.ceil(y / GridTile.tile_height)
        return _x, _y

    def setup_particle_system(self):
        self.particles = ParticleSystem(self, -10)
        player_colours = [(0.0, .5, 0.0), (.5, 0.0, 0.0), (0.0, 0.0, .5), (.5, 0.0, .5)]
        full_player_colours = [(0.0, 1.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 1.0)]
        for p in range(self.max_players):
            self.particle_emitters['tile_activate_' + str(p)] = self.particles.add_emitter(
                3,
                self.media.gfx['medium_particle'],
                shift_pos = 8,
                speed = 3.0,
                spin_speed = 0,
                fade_in_speed = 0.2,
                fade_out_speed = 0.1,
                colour = player_colours[p],
                size = 1.0,
                wait_rate = 5
                )
        for p in range(self.max_players):
            self.particle_emitters['spawn_' + str(p)] = self.particles.add_emitter(
                30,
                self.media.gfx['spawn_particle'],
                shift_pos = 32,
                speed = 4.0,
                spin_speed = 6,
                fade_in_speed = 0.1,
                fade_out_speed = 0.01,
                colour = player_colours[p],
                size = 2.0,
                wait_rate = 5
                )
        for p in range(self.max_players):
            self.particle_emitters['shot_' + str(p)] = self.particles.add_emitter(
                30,
                self.media.gfx['shot_particle'],
                shift_pos = 8,
                speed = 8.0,
                spin_speed = 0,
                fade_in_speed = 0.5,
                fade_out_speed = 0.01,
                colour = full_player_colours[p],
                size = 1.0,
                wait_rate = 5
                )
        for p in range(self.max_players):
            self.particle_emitters['death_' + str(p)] = self.particles.add_emitter(
                20,
                self.media.gfx['death_particle'],
                shift_pos = 32,
                speed = 4.0,
                spin_speed = 0,
                fade_in_speed = 0.5,
                fade_out_speed = 0.005,
                colour = full_player_colours[p],
                size = 2.0,
                wait_rate = 5
                )
        for name in ['footstep1', 'footstep2']:
            self.particle_emitters[name] = self.particles.add_emitter(
                2,
                self.media.gfx[name],
                shift_pos = 32,
                speed = 0.0,
                spin_speed = 0,
                fade_in_speed = .2,
                fade_out_speed = 0.005,
                colour = (.6, .6, .6),
                size = 1.0,
                wait_rate = 10
                )
        self.particle_emitters['bump'] = self.particles.add_emitter(
            20,
            self.media.gfx['bump_particle'],
            shift_pos = 16,
            speed = 5.0,
            spin_speed = 3,
            fade_in_speed = 0.2,
            fade_out_speed = 0.07,
            colour = (1.0, 1.0, 1.0),
            size = 1.0,
            wait_rate = 10
            )

    def tile_claimed(self):
        if self.all_tiles_claimed:
            return
        for x in self.grid.grid:
            for y in self.grid.grid[x]:
                if not self.grid.grid[x][y].claimed:
                    return
        self.all_tiles_claimed = True

    def pressed_start(self):
        for joy in self.input.joys:
            if joy.released_buttons[7]:
                return True
        return False

class GameObjectEntity(Entity):
    def collide_with_player(self, box_size = 60):
        for p_id in self.window.players:
            if p_id == self.player_num or self.window.players[p_id].health < 0 or self.window.players[p_id].respawning:
                continue
            p = self.window.players[p_id]
            half_box_size = box_size / 2
            if self.x > p.x - half_box_size and self.x < p.x + half_box_size and \
                   self.y > p.y - half_box_size and self.y < p.y + half_box_size:
                return p
        return None

    def get_screen_draw_position(self):
        return self.x - self.window.cam_shake[0] - ((self.image.width / 2) * self.scale), self.y - self.window.cam_shake[1] - ((self.image.height / 2) * self.scale)

class PhysicalEntity(Entity):
    """
    Do self.init() at the start of the entity creation and
    self.update() on every frame to ensure the entity updates.
    """
    pos = Vector2d(0.0, 0.0)
    velocity = Vector2d(0.0, 0.0)
    velocity_friction = 0.95
    accel = 0.0
    rotation_velocity = 0
    rotation_friction = 0.9
    rotation_accel = 1.0

    def get_x(self):
        return self.pos.i
    def set_x(self, val):
        self.pos.i = val
    x = property(get_x, set_x)

    def get_y(self):
        return self.pos.j
    def set_y(self, val):
        self.pos.j = val
    y = property(get_y, set_y)

    def init(self):
        self.pos = Vector2d(0.0, 0.0)
        self.velocity = Vector2d(0.0, 0.0)

    def update(self):
        self.update_rotation()
        self.update_velocity()
        self.update_position()

    def update_velocity(self):
        if math.fabs(self.accel) > 0:
            self.velocity += Vector2d(dir = math.radians(self.rotation), mag = self.accel)
        self.velocity *= self.velocity_friction

    def update_position(self):
        self.pos += self.velocity

    def update_rotation(self):
        self.rotation_velocity *= self.rotation_friction
        self.rotation += self.rotation_velocity

    def bump(self, vec):
        self.velocity += vec

class Background(Entity):
    def execute(self, window):
        self.window = window
        for x in range(50):
            BackgroundBits(self.window)
        while True:
            yield

class BackgroundBits(GameObjectEntity):
    def execute(self, window):
        self.window = window
        self.x = random.randint(0, Game.screen_resolution[0])
        self.y = random.randint(0, Game.screen_resolution[1])
        self.z = -1
        self.image = self.window.media.gfx['background']
        self.dir = False
        if random.random() > .5:
            self.dir = True
        self.alpha = 0.0
        self.rotation = random.choice((0, 90, 180, 270))
        self.pulse_time = 1
        self.pulse_dir = False
        self.fade_in = False
        while True:
            if not self.fade_in:
                if self.alpha < .1:
                    self.alpha += .002
                else:
                    self.fade_in = True
            else:
                self.pulse_time -= 1
                if self.pulse_time <= 0:
                    if not self.pulse_dir:
                        if self.alpha < .2:
                            self.alpha += .02
                        else:
                            self.pulse_dir = not self.pulse_dir
                    else:
                        if self.alpha > .1:
                            self.alpha -= .02
                        else:
                            self.pulse_dir = not self.pulse_dir
                            self.pulse_time = random.randint(300, 700)
            if self.dir:
                self.x -= .5
                if self.x < -self.image.width:
                    self.x = Game.screen_resolution[0] + self.image.width
                    self.y = random.randint(0, Game.screen_resolution[1])
            else:
                self.x += .5
                if self.x > Game.screen_resolution[0] + self.image.width:
                    self.x = -self.image.width
                    self.y = random.randint(0, Game.screen_resolution[1])
            yield

class Player(PhysicalEntity, GameObjectEntity):
    anim_time = 0
    base_anim_count = 20
    start_offsets = ((-475, -200), (470, 200), (-475, 200), (470, -200))
    colours = ((.1, 1.0, .1), (1.0, .1, .1), (.1, .1, 1.0), (1.0, .1, 1.0))
    health = 4

    def execute(self, window, player_num, respawn = False):
        self.init()
        self.window = window
        self.player_num = player_num
        self.joy = self.window.input.joys[self.player_num]
        self.health_display = None
        self.respawning = False
        self.x = Game.screen_resolution[0] / 2 + self.start_offsets[player_num][0]
        self.y = Game.screen_resolution[1] / 2 + self.start_offsets[player_num][1]
        self.alpha = 0.0
        if respawn:
            self.respawning = True
        else:
            for i in range(60):
                yield
        self.image = self.window.media.gfx['player']
        self.colour = self.colours[player_num]
        self.health = 4
        self.charged_claim = False
        self.charged_shot = False
        self.shot_dir = 0
        self.bump_cooldown = 0
        self.shot_cooldown = 0
        self.z -5
        for i in range(30):
            yield
        self.window.media.sfx['respawn'].sound.play()
        spawn_point = self.window.particle_emitters['spawn_' + str(self.player_num)].add_point((self.x, self.y), death_timer = 15)
        for frame, total in Game.timer_ticks(15):
            self.alpha = 0.0 if self.alpha else 1.0
            yield
            yield
        self.alpha = 1.0
        self.health_display = HealthDisplay(self.window)
        self.respawning = False
        while True:
            self.handle_movement()
            self.handle_shooting()
            self.grid_pos = self.window.screen_to_grid_pos(self.x, self.y)
            if self.window.grid is None:
                return
            t = self.window.grid.get_tile(*self.grid_pos)
            if not t is None:
                t.activate()
                #if t.claimed_by == self.player_num:
                #    self.velocity *= 0.9
            self.handle_claiming(t)
            self.handle_player_collision()
            self.handle_bumping(t)
            self.cap_speed()
            self.anim()
            yield

    def handle_movement(self):
        speed = 1.5 #.75
        deadzone = .4
        ax = [0,0]
        if self.joy.axes[0] < -deadzone:
            ax[1] = -1
        if self.joy.axes[0] > deadzone:
            ax[1] = 1
        if self.joy.axes[1] < -deadzone:
            ax[0] = -1
        if self.joy.axes[1] > deadzone:
            ax[0] = 1
        if 1 in ax or -1 in ax:
            self.velocity += Vector2d(dir = math.atan2(*ax), mag = speed)
        self.update()
        self.current_speed = max(abs(self.velocity[0]), abs(self.velocity[1]))

    def handle_shooting(self):
        deadzone = .4
        if sys.platform == 'win32':
            h_ax = 4
            v_ax = 3
        else:
            h_ax = 3
            v_ax = 4
        ax = [self.joy.axes[h_ax], self.joy.axes[v_ax]]
        shot_dir = math.degrees(math.atan2(ax[1], ax[0]))

        deadzone = .4
        if (ax[0] < -deadzone or ax[0] > deadzone or \
            ax[1] < -deadzone or ax[1] > deadzone):
            if not self.shot_cooldown and not shot_dir is None:
                self.window.media.sfx['shoot'].sound.play()
                Shot(self.window, self.player_num, shot_dir)
                self.shot_cooldown = 8
        if self.shot_cooldown:
            self.shot_cooldown -= 1

        """
        if self.joy.axes[h_ax] < -deadzone:
            ax[1] = -1
        if self.joy.axes[h_ax] > deadzone:
            ax[1] = 1
        if self.joy.axes[v_ax] < -deadzone:
            ax[0] = -1
        if self.joy.axes[v_ax] > deadzone:
            ax[0] = 1

        if sys.platform == 'win32':
            self.handle_shooting_in_windows(shot_dir)
            return

        if not self.shot_cooldown and not self.charged_shot and self.joy.axes[5] > .5 and not shot_dir is None:
            Shot(self.window, self.player_num, shot_dir)
            self.shot_cooldown = 8
            self.charged_shot = True
        if self.charged_shot and self.joy.axes[5] < -.5:
            self.charged_shot = False
        if self.shot_cooldown:
            self.shot_cooldown -= 1
        """

    def handle_shooting_in_windows(self, shot_dir):
        if not self.shot_cooldown and not shot_dir is None and self.joy.released_buttons[5]:
            Shot(self.window, self.player_num, shot_dir)
            self.shot_cooldown = 8
        if self.shot_cooldown:
            self.shot_cooldown -= 1

    def handle_claiming(self, tile):
        if tile is None:
            return
        tile.claim(self.player_num)
        self.window.tile_claimed()
        """
        if sys.platform == 'win32':
            self.handle_claiming_in_windows(tile)
            return
        if self.joy.axes[2] > 0:
            self.charged_claim = True
        if self.charged_claim and self.joy.axes[2] < -.5:
            self.charged_claim = False
            tile.claim(self.player_num)
            self.window.tile_claimed()
        """

    def handle_claiming_in_windows(self, tile):
        if self.joy.released_buttons[4]:
            tile.claim(self.player_num)
            self.window.tile_claimed()

    def handle_bumping(self, tile):
        if self.bump_cooldown:
            self.bump_cooldown -= 1
        if not tile is None:
            return
        bump_amount = 10.0
        d = 0
        if self.grid_pos[0] < 0:
            d = 0
        elif self.grid_pos[0] >= self.window.grid.grid_size[0]:
            d = 180
        elif self.grid_pos[1] < 0:
            d = 90
        elif self.grid_pos[1] >= self.window.grid.grid_size[1]:
            d = -90
        self.velocity = Vector2d(0.0, 0.0)
        self.bump(Vector2d(dir = math.radians(d), mag = 35.0))#6.5 * self.current_speed))
        if self.bump_cooldown == 0:
            self.window.do_cam_shake(15)
            random.choice(self.window.media.sfx['hurt']).sound.play()
            self.window.media.sfx['bounce'].sound.play()
            self.window.particle_emitters['bump'].add_point((self.x, self.y), death_timer = 5)
            self.bump_cooldown = 5

    def handle_player_collision(self):
        p = self.collide_with_player(box_size = 64)
        if not p is None:
            angle_between = Game.angle_between_points((self.x, self.y), (p.x, p.y))
            self.window.do_cam_shake(5)
            p.bump(Vector2d(dir = math.radians(float(angle_between)), mag = 15.0))
            self.bump(Vector2d(dir = math.radians(float(angle_between)), mag = -15.0))
            random.choice(self.window.media.sfx['hurt']).sound.play()
            self.window.media.sfx['bounce'].sound.play()

    def cap_speed(self):
        cap = 60.0
        if self.velocity.i < -cap:
            self.velocity = Vector2d(-cap, self.velocity.j)
        if self.velocity.i > cap:
            self.velocity = Vector2d(cap, self.velocity.j)
        if self.velocity.j < -cap:
            self.velocity = Vector2d(self.velocity.i, -cap)
        if self.velocity.j > cap:
            self.velocity = Vector2d(self.velocity.i, cap)

    def hit_by_shot(self):
        self.health -= 1
        self.health_display.show()
        random.choice(self.window.media.sfx['hurt']).sound.play()
        if self.health < 0:
            self.die()
            self.window.do_cam_shake(100)
            self.window.respawn_player(self.player_num)

    def die(self):
        self.window.media.sfx['death'].sound.play()
        self.window.particle_emitters['death_' + str(self.player_num)].add_point((self.x, self.y), death_timer = 20)
        for x in range(30):
            PlayerChunk(self.window, self.player_num)
        self.destroy()

    def on_exit(self):
        if not self.health_display is None:
            self.health_display.die()

    def anim(self):
        self.anim_time += 1
        if self.anim_time > max(3, self.base_anim_count - (5 * self.current_speed)):
            if self.image_seq == 3:
                self.image_seq = 0
            else:
                self.image_seq += 1
            self.anim_time = 0
            if self.current_speed > .5:
                if random.random() > .5:
                    self.window.particle_emitters['footstep1'].add_point((self.x, self.y), death_timer = 10)
                else:
                    self.window.particle_emitters['footstep2'].add_point((self.x, self.y), death_timer = 10)

class PlayerChunk(PhysicalEntity, GameObjectEntity):
    def execute(self, window, player_num):
        self.window = window
        self.player_num = player_num
        self.player = self.window.players[player_num]
        self.image = self.window.media.gfx['player_chunk']
        self.init()
        self.x, self.y = self.player.x, self.player.y
        self.colour = self.player.colour
        self.rotation = random.randint(0, 360)
        self.velocity += Vector2d(dir = math.radians(self.rotation), mag = random.randint(10, 20))
        for x in range(60):
            self.update()
            yield
        while self.alpha > 0.0:
            self.alpha -= .05
            self.update()
            yield
        self.destroy()

class HealthDisplay(Entity):
    def execute(self, window):
        self.window = window
        self.image = self.window.media.gfx['health']
        self.z = -10
        self.do_show = False
        self.do_die = False
        self.show_count = 0
        self.alpha = 0.0
        while True:
            self.update()
            if self.do_show:
                while self.show_count > 0:
                    if self.alpha < 1.0:
                        self.alpha += .1
                    self.show_count -= 1
                    self.update()
                    if self.do_die:
                        break
                    yield
                self.do_show = False
            else:
                if self.alpha > 0.0:
                    self.alpha -= .1
            if self.do_die:
                if self.alpha > 0.0:
                    self.alpha -= .1
                else:
                    self.destroy()
            yield

    def die(self):
        self.do_die = True

    def update(self):
        self.x = self.parent.x + 25
        self.y = self.parent.y - 32
        self.image_seq = max(0, self.parent.health)

    def show(self):
        self.do_show = True
        self.show_count = 30

class Shot(GameObjectEntity):
    def execute(self, window, player_num, rotation):
        self.window = window
        self.player_num = player_num
        self.rotation = rotation
        self.x, self.y = self.parent.x, self.parent.y
        self.z = -2
        self.colour = self.parent.colour
        self.blend = True
        self.image = self.window.media.gfx['shot']
        while True:
            self.move_forward(18.0)
            self.grid_pos = self.window.screen_to_grid_pos(self.x, self.y)
            t = self.window.grid.get_tile(*self.grid_pos)
            if t is None:
                self.alpha -= .2
                if self.alpha < 0.0:
                    self.destroy()
            else:
                p = self.collide_with_player()
                if not p is None:
                    angle_between = Game.angle_between_points((self.x, self.y), (p.x, p.y))
                    p.bump(Vector2d(dir = math.radians(float(angle_between)), mag = 10.0))
                    self.window.do_cam_shake(10)
                    p.hit_by_shot()
                    self.window.particle_emitters['shot_' + str(p.player_num)].add_point((self.x, self.y), death_timer = 5)
                    while self.scale > 0:
                        self.scale -= .2
                        yield
                    self.destroy()
            self.move_forward(10.0)
            yield

class Grid(Entity):
    grid = {}
    origin_screen_pos = (110, 130)
    grid_size = 25, 11
    initialised = False
    done_intro_anim = False

    def execute(self, window):
        self.window = window
        self.z = 0
        self.rev_anim = False
        self.do_die = False
        while True:
            if self.initialised and not self.done_intro_anim:
                for x in self.grid:
                    for y in self.grid[x]:
                        self.grid[x][y].switch_on()
                    yield
                self.done_intro_anim = True
                self.parent.start_game()
            if self.initialised:
                if not self.window.all_tiles_claimed:
                    for x in range(60):
                        yield
                gk = list(self.grid.keys())
                if self.rev_anim:
                    gk.reverse()
                self.rev_anim = not self.rev_anim
                for x in gk:
                    for y in self.grid[x]:
                        self.grid[x][y].activate()
                    yield
            while self.do_die:
                for x in range(3):
                    if not len(self.tiles):
                        continue
                    tile = self.tiles.pop()
                    tile.die()
                if not len(self.tiles):
                    self.window.change_state(Window.STATE_SCORES)
                    self.destroy()
                yield
            yield

    def die(self):
        self.do_die = True
        random.shuffle(self.tiles)

    def init(self):
        self.tiles = []
        for x in range(self.grid_size[0]):
            self.grid[x] = {}
            for y in range(self.grid_size[1]):
                self.grid[x][y] = GridTile(self.window, (x, y))
                self.grid[x][y].alpha = 0.0
                self.tiles.append(self.grid[x][y])
        self.initialised = True

    def get_tile(self, x, y):
        if not x in self.grid:
            return None
        if not y in self.grid[x]:
            return None
        return self.grid[x][y]

class GridTile(GameObjectEntity):
    tile_width = 63
    tile_height = 56
    on = 0
    claim_colours = ((.6, 1.0, .6), (1.0, .6, .6), (.6, .6, 1.0), (1.0, .6, 1.0))

    def execute(self, window, grid_pos):
        self.window = window
        self.grid_pos = grid_pos
        self.image = self.window.media.gfx['grid']
        self.x, self.y = self.window.grid_pos_to_screen(*self.grid_pos)
        if self.grid_pos[0] % 2:
            self.y -= self.tile_height / 2
        self.colour = (.5, .5, 1.0)
        self.z = self.window.grid.z
        self.claimed_seq = random.randint(2, 5)
        self.claimed = False
        self.claimed_by = -1
        self.image_seq = 1
        self.image_seq_overlay = None
        self.do_die = False
        while True:
            while not self.on:
                if self.on == 1:
                    while self.alpha < 1.0:
                        self.alpha += .25
                        yield
                    self.on = 2
                yield
            self.alpha_to = .6
            if self.alpha > self.alpha_to:
                self.alpha -= .05
            if self.alpha < self.alpha_to:
                self.alpha += .05
            if self.do_die:
                for frame, total in Game.timer_ticks(10):
                    self.scale = Game.slerp(1.0, 0.0, frame / total)
                    yield
                self.destroy()
            yield

    def die(self):
        self.do_die = True

    def switch_on(self):
        self.on = 1

    def activate(self):
        self.alpha_to = 1.0
        self.alpha = 1.0

    def claim(self, player_num):
        if self.claimed and self.claimed_by == player_num:
            return
        self.claimed_by = player_num
        if self.image_seq == 1 and self.image_seq_overlay is None:
            self.image_seq_overlay = GridTileSeqOverlap(self.window, self)
        self.colour = self.claim_colours[player_num]
        self.window.particle_emitters['tile_activate_' + str(player_num)].add_point((self.x, self.y), death_timer = 15)
        self.claimed = True

class GridTileSeqOverlap(GameObjectEntity):
    def execute(self, window, tile):
        self.window = window
        #self.tile = tile
        #self.x, self.y, self.z = tile.x, tile.y, -3
        tile.image_seq = tile.claimed_seq
        tile.alpha = 1.0
        self.destroy()
        yield
        return
        self.colour = tile.claim_colours[tile.claimed_by]
        self.alpha = 0.0
        tile_alpha = .6
        while self.alpha < 1.0:
            self.alpha += .1
            tile_alpha -= .1
            tile.alpha = tile_alpha
            yield
        tile.image_seq = self.image_seq
        tile.image_seq_overlay = None
        tile.alpha = 1.0
        self.destroy()

class Timer(Entity):
    def execute(self, window):
        self.window = window
        self.time = self.window.timer_length
        self.timer_display = None
        for frame, total in Game.timer_ticks(60):
            yield        
        while True:
            for frame, total in Game.timer_ticks(30):
                yield
            self.time -= 1
            if self.timer_display:
                self.timer_display.switch_state("state_pulse", self.time)
            else:
                if self.time <= self.window.timer_last_section:
                    self.timer_display = TimerDisplay(self.window)
                    self.window.media.sfx['timewarning'].sound.play(loops = -1)
            if not self.time:
                break
        self.window.end_timer()
        self.timer_display.switch_state("state_die")
        while self.timer_display.is_alive():
            yield
                
    def on_exit(self):
        self.timer_display.destroy()
                    
class TimerDisplay(Entity):
    def execute(self, window):
        self.window = window
        self.time = self.parent.time
        self.text = Game.write_text((Game.screen_resolution[0] / 2), 30, font = self.window.media.fnt['timer'], text = str(self.time), alignment = ALIGN_CENTRE)
        self.text.z = -20
        self.text.alpha = 0.0
        self.text.scale_point = (self.text.text_image_size[0] / 2, self.text.text_image_size[1] / 2)
        for frame, total in Game.timer_ticks(30):
            self.text.alpha = Game.lerp(0.0, 1.0, frame / total)
            yield
        yield self.switch_state("state_normal")

    def state_normal(self):
        while True:
            yield

    def state_pulse(self, time):
        self.time = time
        self.text.text = str(time)
        for frame, total in Game.timer_ticks(30):
            self.text.scale = Game.lerp(1.2, 1.0, frame / total)
            yield
        yield self.switch_state("state_normal")

    def state_die(self):
        for frame, total in Game.timer_ticks(30):
            self.text.alpha = Game.lerp(1.0, 0.0, frame / total)
            yield
        self.text.destroy()

class ScoreBoard(Entity):
    def execute(self, window):
        self.window = window
        self.shown_score = False
        self.press_start_text = None
        self.objs = []
        for frame, total in Game.timer_ticks(20):
            yield
        for x in range(Window.max_players):
            self.objs.append(ScoreBoardPlayer(self.window, x))
        for frame, total in Game.timer_ticks(50):
            yield
        while True:
            if self.shown_score:
                if self.press_start_text is None:
                    self.press_start_text = Game.write_text((Game.screen_resolution[0] / 2), Game.screen_resolution[1] - 100, font = self.window.media.fnt['score_press_start'], text = "- press start -", alignment = ALIGN_CENTRE)
                    for frame, total in Game.timer_ticks(30):
                        self.press_start_text.alpha = Game.slerp(0.0, 1.0, frame / total)
                        yield
                for joy in self.window.input.joys:
                    if joy.released_buttons[7]:
                        self.window.media.sfx['pressstart'].sound.play()
                        for frame, total in Game.timer_ticks(20):
                            self.press_start_text.alpha = Game.slerp(1.0, 0.0, frame / total)
                            yield
                        for frame, total in Game.timer_ticks(10):
                            for x in self.objs:
                                x.alpha = Game.slerp(x.alpha_to, 0.0, frame / total)
                            yield
                        self.destroy()
                        self.window.change_state(Window.STATE_TITLE)
            yield

    def on_exit(self):
        self.press_start_text.destroy()
        for x in self.objs:
            x.destroy()

class ScoreBoardPlayer(GameObjectEntity):
    start_offsets = ((-300, 0), (-100, 0), (100, 0), (300, 0))
    def execute(self, window, player_num):
        self.window = window
        self.player_num = player_num
        self.z = -10
        self.image = self.window.media.gfx['player']
        self.x = Game.screen_resolution[0] / 2 + self.start_offsets[self.player_num][0]
        self.y = Game.screen_resolution[1] / 2 + self.start_offsets[self.player_num][1] - 50
        self.anim_time = 0
        self.alpha = 0.0
        self.alpha_to = .10
        self.blend = True
        if self.player_num in self.window.player_scores:
            self.colour = Player.colours[self.player_num]
            self.alpha_to = .95
        for frame, total in Game.timer_ticks(60):
            self.alpha = Game.slerp(0.0, self.alpha_to, frame / total)
            self.anim()
            yield
        self.score_text = None
        if self.player_num in self.window.player_scores:
            self.score_text = ScoreBoardScore(self.window, self, self.window.player_scores[self.player_num])
        self.parent.shown_score = True
        while True:
            self.anim()
            yield

    def anim(self):
        self.anim_time += 1
        if self.anim_time > 5:
            if self.image_seq == 3:
                self.image_seq = 0
            else:
                self.image_seq += 1
            self.anim_time = 0

    def on_exit(self):
        if not self.score_text is None:
            self.score_text.destroy()

class ScoreBoardScore(Entity):
    def execute(self, window, player_marker, score):
        self.window = window
        self.player_marker = player_marker
        self.score = score
        self.x = self.player_marker.x
        self.y = self.player_marker.y + 75
        self.text = Game.write_text(self.x, self.y, text = self.score, font = self.window.media.fnt['final_score'], alignment = ALIGN_CENTRE)
        self.text.z = -10
        self.text.colour = (.2, .2, .2)
        scale_to = .5
        if self.is_top_score():
            self.text.colour = (1.0, 1.0, 1.0)
            scale_to = 1.0
        self.text.scale_point = (self.text.text_image_size[0] / 2, self.text.text_image_size[1] / 2)
        for frame, total in Game.timer_ticks(10):
            self.text.alpha = Game.slerp(0.0, 1.0, frame / total)
            self.text.scale = Game.slerp(0.5, 1.3, frame / total)
            yield
        for frame, total in Game.timer_ticks(40):
            self.text.scale = Game.slerp(1.3, scale_to, frame / total)
            yield
        while True:
            self.text.alpha = self.player_marker.alpha
            yield

    def is_top_score(self):
        s = []
        for p_id in self.window.player_scores:
            s.append(self.window.player_scores[p_id])
        s.sort()
        if s[-1] == self.score:
            return True
        return False

    def on_exit(self):
        self.text.destroy()

class Title(Entity):
    def execute(self, window):
        self.window = window
        self.text = Game.write_text(Game.screen_resolution[0] / 2, Game.screen_resolution[1] / 2, text = "d  i  a  g  o  n  e  x", font = self.window.media.fnt['title_name'], alignment = ALIGN_CENTRE)
        self.text.z = -10
        self.text.alpha = 0.0
        self.window.media.mus['title'].sound.play(loops = -1)
        for frame, total in Game.timer_ticks(30):
            yield
        for frame, total in Game.timer_ticks(30):
            self.text.alpha = Game.lerp(0.0, 1.0, frame / total)
            yield
        self.text2 = Game.write_text(Game.screen_resolution[0] / 2, (Game.screen_resolution[1] / 2) + 200, text = "press start", font = self.window.media.fnt['title_press_start'], alignment = ALIGN_CENTRE)
        self.text2.z = -10
        self.text2.alpha = 0.0
        for frame, total in Game.timer_ticks(30):
            self.text2.alpha = Game.slerp(0.0, 1.0, frame / total)
            yield
        while True:
            if self.window.pressed_start():
                self.window.media.sfx['pressstart'].sound.play()
                break
            yield
        for frame, total in Game.timer_ticks(20):
            self.text.alpha = Game.slerp(1.0, 0.0, frame / total)
            self.text2.alpha = Game.slerp(1.0, 0.0, frame / total)
            yield
        self.window.change_state(Window.STATE_SELECT_PLAYERS)
        self.destroy()

    def on_exit(self):
        self.text.destroy()
        self.text2.destroy()

class PlayerSelect(Entity):
    def execute(self, window):
        self.window = window
        self.window.selected_players = []
        self.objs = []
        for x in range(Window.max_players):
            if x < len(self.window.input.joys):
                self.objs.append(PlayerSelectPlayer(self.window, x))
        self.text = Game.write_text(Game.screen_resolution[0] / 2, (Game.screen_resolution[1] / 2) - 200, text = "press buttons to register", font = self.window.media.fnt['player_select_press_buttons'], alignment = ALIGN_CENTRE)
        self.text.z = -10
        self.text.alpha = 0.0
        for frame, total in Game.timer_ticks(15):
            self.text.alpha = Game.slerp(0.0, 1.0, frame / total)
            yield
        self.text2 = None
        while True:
            if len(self.window.selected_players) > 1:
                if self.text2 is None:
                    self.text2 = Game.write_text(Game.screen_resolution[0] / 2, (Game.screen_resolution[1] / 2) + 200, text = "press start", font = self.window.media.fnt['player_select_press_buttons'], alignment = ALIGN_CENTRE)
                    self.text2.z = -10
                    self.text2.alpha = 0.0
                    for frame, total in Game.timer_ticks(10):
                        self.text2.alpha = Game.slerp(0.0, 1.0, frame / total)
                        yield
                if self.window.pressed_start():
                    self.window.media.sfx['pressstart'].sound.play()
                    self.window.media.mus['title'].sound.fadeout(2000)
                    for x in self.objs:
                        x.die()
                    for frame, total in Game.timer_ticks(20):
                        self.text.alpha = Game.slerp(1.0, 0.0, frame / total)
                        self.text2.alpha = Game.slerp(1.0, 0.0, frame / total)
                        yield
                    self.window.change_state(Window.STATE_PLAYING)
                    self.destroy()
            yield

    def on_exit(self):
        self.text.destroy()
        self.text2.destroy()
        for x in self.objs:
            x.destroy()

class PlayerSelectPlayer(GameObjectEntity):
    start_offsets = ((-300, 0), (-100, 0), (100, 0), (300, 0))
    def execute(self, window, player_num):
        self.window = window
        self.player_num = player_num
        self.z = -10
        self.image = self.window.media.gfx['player']
        self.x = Game.screen_resolution[0] / 2 + self.start_offsets[self.player_num][0]
        self.y = Game.screen_resolution[1] / 2 + self.start_offsets[self.player_num][1]
        self.anim_time = 0
        self.alpha = 0.0
        self.colour = Player.colours[self.player_num]
        self.selected = False
        self.do_die = False
        while True:
            if not self.selected:
                for k,v in enumerate(self.window.input.joys[self.player_num].released_buttons):
                    if k == 7:
                        continue
                    if v or (player_num == 2 and Game.keyboard_key_released(K_SPACE)):
                        self.window.media.sfx['playerregister'].sound.play()
                        for frame, total in Game.timer_ticks(15):
                            self.alpha = Game.slerp(0.0, 0.95, frame / total)
                            self.anim()
                            yield
                        self.selected = True
                        self.window.selected_players.append(self.player_num)
            else:
                if self.do_die:
                    for frame, total in Game.timer_ticks(10):
                        self.alpha = Game.slerp(0.0, 0.95, frame / total)
                        self.anim()
                        yield
                    self.destroy()
            self.anim()
            yield

    def die(self):
        self.do_die = True

    def anim(self):
        self.anim_time += 1
        if self.anim_time > 5:
            if self.image_seq == 3:
                self.image_seq = 0
            else:
                self.image_seq += 1
            self.anim_time = 0

Game.screen_resolution = (1366, 768)
Game.full_screen = False
Game.modules_enabled = ('Entity_Helper',)
Game.target_fps = 30
Window()
