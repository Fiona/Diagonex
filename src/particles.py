"""
LD31 o'clock
Entire Game On One Screen
Partiiicleeeeeeeees
"""

# System imports
import random
from OpenGL.GL import *

# Myrmidon imports
from myrmidon import Game, Entity
from myrmidon.consts import *


class ParticleSystem(Entity):
    def execute(self, game, z):
        self.emitters = []
        self.game = game
        self.z = z
        self.time = 0
        while True:
            self.time+= 1
            yield

    def add_emitter(self, rate, texture, shift_pos = 50, speed = 2.0, spin_speed = 0, fade_in_speed = 0.1, fade_out_speed = 0.1, wait_rate = None, size = 1.0, colour = (1.0, 1.0, 1.0), angle_from = 0, angle_to = 360):
        em = ParticleEmitter(self.game, self, rate, texture, shift_pos, speed, spin_speed, fade_in_speed, fade_out_speed, wait_rate, size, colour, angle_from, angle_to)
        self.emitters.append(em)
        return em

    def remove_emitter(self, emitter):
        self.emitters.remove(emitter)
        
    def draw(self):
        if self.time <= 60:
            return
        for em in self.emitters:
            em.produce_particles()
            em.update_and_draw_particles()
        
class ParticleEmitter(object):
    def __init__(self, game, particle_system, rate, texture, shift_pos, speed, spin_speed, fade_in_speed, fade_out_speed, wait_rate, size, colour, angle_from, angle_to):
        self.particle_system = particle_system
        self.game = game
        self.points = set()
        self.rate = rate
        self.texture = texture
        self.shift_pos = shift_pos
        self.speed = speed
        self.spin_speed = spin_speed
        self.fade_in_speed = fade_in_speed
        self.fade_out_speed = fade_out_speed
        self.wait_rate = wait_rate
        self.size = size
        self.colour = colour
        self.angle_from = angle_from
        self.angle_to = angle_to
        self.particles = set()

    def add_point(self, pos, rate = None, death_timer = None):
        p = ParticleEmitterPoints(pos, self.wait_rate, self.angle_from, self.angle_to, rate, death_timer)
        self.points.add(p)
        return p

    def remove_point(self, point):
        self.points.remove(point)
        
    def produce_particles(self):
        if not self.particle_system._executing:
            return
        remove = []
        for p in self.points:
            p.life += 1
            if not p.death_timer == None and p.life == p.death_timer:
                remove.append(p)
                continue
            if p.stop_producing_particles:
                continue
            if not p.wait_rate == None:
                if p.wait < p.wait_rate:
                    p.wait += 1
                    continue
                p.wait = 0
            for i in range(self.rate if p.rate == None else p.rate):
                angle = random.randrange(p.angle_from, p.angle_to)
                pos = p.pos
                if self.shift_pos > 0:
                    pos = Game.move_forward(pos, random.randrange(0, self.shift_pos), angle)
                self.particles.add(Particle(pos, 0.0, angle, 0))

        for p in remove:
            self.points.remove(p)
                                
    def update_and_draw_particles(self):
        glPushMatrix()
        glEnable(GL_POINT_SPRITE)
        glTexEnvf(GL_POINT_SPRITE, GL_COORD_REPLACE, GL_TRUE)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.texture.surface)
        Game.engine['gfx'].last_image = self.texture.surface
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glPointSize(self.texture.width * self.size)
        glBegin(GL_POINTS)

        to_remove = []          
        for x in self.particles:
            if self.particle_system._executing:
                x.pos = Game.move_forward(x.pos, self.speed, x.angle)
                if self.spin_speed:
                    x.angle += self.spin_speed
            if x.alpha > 0.0:
                glColor4f(self.colour[0],self.colour[1],self.colour[2],x.alpha)
                glVertex2f(x.pos[0], x.pos[1])
            if self.particle_system._executing:
                if x.mode == 0:
                    x.alpha += self.fade_in_speed
                    if x.alpha >= 0.5:
                        x.mode = 1
                else:
                    x.alpha -= self.fade_out_speed
                if x.alpha <= 0.0:
                    to_remove.append(x)
                    
        for x in to_remove:
            self.particles.remove(x)            

        glEnd()
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_POINT_SPRITE)
        glPopMatrix()

class ParticleEmitterPoints(object):
    def __init__(self, pos, wait_rate, angle_from, angle_to, rate = None, death_timer = None):
        self.pos = pos
        self.wait_rate = wait_rate
        self.wait = wait_rate
        self.rate = rate
        self.death_timer = death_timer
        self.stop_producing_particles = False
        self.angle_from = angle_from
        self.angle_to = angle_to
        self.life = 0

class Particle(object):
    pos = (0,0)
    alpha = 0.0
    angle = 0
    mode = 0
    def __init__(self, pos, alpha, angle, mode):
        self.pos = pos
        self.alpha = alpha
        self.angle = angle
        self.mode = mode
