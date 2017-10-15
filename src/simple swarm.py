# Adapted from code by Tom Marble
# https://github.com/tmarble/pyboids/blob/master/boids.py

import random
import pygame
import pygame.locals as pyg
from pygame.math import Vector3
import OpenGL.GL as gl
import OpenGL.GLU as glu

"""
TODO:
- implement basic swarming behaviour constrained in a cube
    - think about attractors and predators when so doing
"""

# GLOBALS
cube_min = Vector3(0, 0, 0)  # cube min vertex
edge_length = 30.0
camera_pos = Vector3(0.5 * edge_length, 0.5 * edge_length, 2.5 * edge_length)
focal_point = Vector3(0.5 * edge_length, 0.5 * edge_length, 0.5 * edge_length)


def random_range(lower=0.0, upper=1.0):
    """return a random number between lower and upper"""
    return lower + (random.random() * (upper - lower))


def random_vector3(lower=0.0, upper=1.0):
    """return a Vector3 with random elements between lower and upper"""
    return Vector3(random_range(lower, upper),
                   random_range(lower, upper),
                   random_range(lower, upper))


class Rule(object):
    """
    Template for rules of flocking
    """

    def __init__(self):
        self.change = Vector3(0.0, 0.0, 0.0)    # velocity correction
        self.num = 0                            # number of participants
        self.neighbourhood = 5.0                # number of boids to account for around one boid

    @staticmethod
    def accumulate(self, boid, other, distance):
        """ save any corrections based on other boid to self.change """
        pass

    @staticmethod
    def add_adjustment(self, boid):
        """ add the accumulated self.change to boid.adjustment """
        pass


class Cohesion(Rule):
    """ Rule 1: Boids try to fly towards the centre of mass of neighbouring boids. """

    def __init__(self):
        super().__init__()
        self.neighbourhood = 25.0

    def accumulate(self, boid, other, distance):
        """ save any cohesion corrections based on other boid to self.change """
        if other != boid:
            self.change = self.change + other.location
            self.num += 1

    def add_adjustment(self, boid):
        """ add the accumulated self.change to boid.adjustment """
        if self.num > 0:
            centroid = self.change / self.num
            desired = centroid - boid.location
            self.change = (desired - boid.velocity) * 0.0006
        boid.adjustment = boid.adjustment + self.change


class Alignment(Rule):
    """ Rule 2: Boids try to match velocity with near boids. """

    def __init__(self):
        super().__init__()
        self.neighbourhood = 10.0  # operating area for this correction

    def accumulate(self, boid, other, distance):
        """ save any alignment corrections based on other boid to self.change """
        if other != boid:
            self.change = self.change + other.velocity
            self.num += 1

    def add_adjustment(self, boid):
        """ add the accumulated self.change to boid.adjustment """
        if self.num > 0:
            group_velocity = self.change / self.num
            self.change = (group_velocity - boid.velocity) * 0.03
        boid.adjustment = boid.adjustment + self.change


class Separation(Rule):
    """ Rule 3: Boids try to keep a small distance away from other objects (including other boids). """

    def __init__(self):
        super().__init__()

    def accumulate(self, boid, other, distance):
        """save any separation corrections based on other boid to self.change"""
        if other != boid:
            separation = boid.location - other.location
            if separation.length() > 0:
                self.change = self.change + (separation.normalize() / distance)
            self.num += 1

    def add_adjustment(self, boid):
        """add the accumulated self.change to boid.adjustment"""
        if self.change.length() > 0:
            group_separation = self.change / self.num
            self.change = (group_separation - boid.velocity) * 0.01
        boid.adjustment = boid.adjustment + self.change

# TODO rule for constaining to cube


class Boid(object):
    """
    A single swarm agent
    """

    def __init__(self):
        self.color = random_vector3(0.5)  # R G B
        self.location = focal_point
        # TODO start at random locations (and remove 'centre')
        self.velocity = random_vector3(-1.0, 1.0)  # vx vy vz
        self.adjustment = Vector3(0.0, 0.0, 0.0)  # to accumulate corrections

    def __repr__(self):
        # TODO
        return "TODO - Boid"

    def calc_v(self, all_boids):
        """
        Calculate velocity for next tick by applying the three basic swarming rules
        """
        # Apply the rules to each of the boids
        rules = [Cohesion(), Alignment(), Separation()]
        for boid in all_boids:
            distance = self.location.distance_to(boid.location)
            for rule in rules:
                if distance < rule.neighbourhood:
                    rule.accumulate(self, boid, distance)
        self.adjustment = Vector3(0.0, 0.0, 0.0)  # reset adjustment vector
        for rule in rules:  # save corrections to the adjustment
            rule.add_adjustment(self)

    def limit_speed(self, max_speed):
        """ensure the speed does not exceed max_speed"""
        if self.velocity.length() > max_speed:
            self.velocity = self.velocity.normalize() * max_speed

    def render(self):
        """
        Draw this boid
        """
        # TODO make it cooler than just a line
        gl.glBegin(gl.GL_LINES)
        gl.glColor(self.color.x, self.color.y, self.color.z)
        gl.glVertex(self.location.x, self.location.y, self.location.z)
        if self.velocity.length() > 0:
            head = self.location + self.velocity.normalize() * 2.5
        else:
            head = self.location
        gl.glVertex(head.x, head.y, head.z)
        gl.glEnd()

    def update(self):
        """
        Move to new position using calculated velocity
        """
        velocity = self.velocity + self.adjustment
        # Add a constant velocity in whatever direction
        # they are moving so they don't ever stop.
        if velocity.length() > 0:
            velocity = velocity + (velocity.normalize() * random_range(0.0, 0.007))
        self.velocity = velocity
        self.limit_speed(1.0)
        self.location = self.location + self.velocity


class Swarm(object):
    """
    A swarm of boids
    """

    def __init__(self, num_boids):
        self.num_boids = num_boids
        self.boids = []
        for _ in range(num_boids):
            self.boids.append(Boid())

    def __repr__(self):
        return "TODO - Swarm"

    def render(self):
        # TODO
        for boid in self.boids:
            boid.render()

    def update(self):
        # TODO
        for boid in self.boids:
            boid.calc_v(self.boids)
        for boid in self.boids:  # TODO is this line necessary? (calc all v first or one at a time?)
            boid.update()


class Renderer(object):
    """
    Contains the swarm object(s) and renders everything
    TODO should be able to accept more than one swarm
    """

    def __init__(self, swarms):
        self.x0 = cube_min.x
        self.y0 = cube_min.y
        self.z0 = cube_min.z
        self.x1 = self.x0 + edge_length
        self.y1 = self.y0 + edge_length
        self.z1 = self.z0 + edge_length

        self.swarms = swarms
        self.edge_length = edge_length

    def __repr__(self):
        return "TODO - Renderer"

    def top_square(self):
        """
        :return: Array of points that make up the top of the cube
        """
        return [[self.x0, self.y1, self.z0],
                [self.x1, self.y1, self.z0],
                [self.x1, self.y1, self.z1],
                [self.x0, self.y1, self.z1]]

    def bottom_square(self):
        """
        :return: Array of points that make up the bottom of the cube
        """
        return [[self.x0, self.y0, self.z0],
                [self.x1, self.y0, self.z0],
                [self.x1, self.y0, self.z1],
                [self.x0, self.y0, self.z1]]

    def render_cube(self):
        """ Draw the bounding box """
        # TODO make more elegant
        gl.glColor(0.5, 0.5, 0.5)
        # XY plane, positive Z
        gl.glBegin(gl.GL_LINE_LOOP)
        for point in self.top_square():
            gl.glVertex(point)
        gl.glEnd()
        # XY plane, negative Z
        gl.glBegin(gl.GL_LINE_LOOP)
        for point in self.bottom_square():
            gl.glVertex(point)
        gl.glEnd()
        # The connecting lines in the Z direction
        gl.glBegin(gl.GL_LINES)
        for (point1, point2) in zip(self.top_square(), self.bottom_square()):
            gl.glVertex(point1)
            gl.glVertex(point2)
        gl.glEnd()

    def render(self):
        """
        Render everything
        """
        self.render_cube()
        for swarm in self.swarms:
            swarm.render()

    def update(self):
        """
        Update all the swarms
        """
        for swarm in self.swarms:
            swarm.update()


def main():
    # TODO I don't get most of this, it's just boring setup code. Mostly Tom Marble:
    # set up display window
    title = "Swarm Music Demo v.-1000"
    window_size = 700
    xy_ratio = 1  # x side / y side
    camera_rotation = 0.1
    rotation_delay = 0
    # random.seed(72)  # for repeatability

    pygame.init()
    pygame.display.set_caption(title, title)
    pygame.display.set_mode((window_size, window_size), pyg.OPENGL | pyg.DOUBLEBUF)
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glClearColor(0, 0, 0, 0)
    # set up the camera
    gl.glMatrixMode(gl.GL_PROJECTION)
    gl.glLoadIdentity()
    glu.gluPerspective(edge_length * 2, xy_ratio, 1.0, (6 * edge_length) + 10)  # setup lens
    gl.glMatrixMode(gl.GL_MODELVIEW)
    gl.glLoadIdentity()
    # look at the middle of the cube
    glu.gluLookAt(camera_pos.x, camera_pos.y, camera_pos.z, focal_point.x, focal_point.y, focal_point.z, 0.0, 1.0, 0.0)
    # diameter of rasterised points
    gl.glPointSize(3.0)

    swarm = Swarm(50)
    renderer = Renderer([swarm])

    while True:
        event = pygame.event.poll()
        if event.type == pyg.QUIT or (event.type == pyg.KEYDOWN and
            (event.key == pyg.K_ESCAPE or event.key == pyg.K_q)):
            break
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        renderer.render()
        # gl.glRotatef(camera_rotation, 0, 1, 0)  # orbit camera around by angle
        pygame.display.flip()  # update screen
        if rotation_delay > 0:
            pygame.time.wait(rotation_delay)
        renderer.update()

if __name__ == '__main__':
    main()
