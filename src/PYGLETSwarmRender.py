import pyglet
import pyglet.gl as gl

# TODO temp
import random
import Swarm
from vectors import Vector3

"""
Render the swarm objects
Contains render methods for the displayable classes
"""

# constants
UPDATE_RATE = 100  # Hz
FILL = False

# colours
dark_gray = (.75, .75, .75, 1)
white     = (1.0, 1.0, 1.0, 1)
red       = (1.0, 0.0, 0.0, 1)
green     = (0.0, 1.0, 0.0, 1)
blue      = (0.0, 0.0, 1.0, 1)


class OBJModel:
    """
    Represents an OBJ model.
    """

    def __init__(self, coords=(0, 0, 0), scale=1, color=dark_gray, path=None):
        self.vertices = []
        self.quad_indices = []
        self.triangle_indices = []

        # translation and rotation values
        [self.x, self.y, self.z] = coords
        self.rx = self.ry = self.rz = 0
        self.scale = scale

        # color of the model
        self.color = color

        # if path is provided
        if path:
            self.load(path)

    def clear(self):
        # not sure why this is necessary (doesn't seem to be)
        self.vertices = self.vertices[:]
        self.quad_indices = self.quad_indices[:]
        self.triangle_indices = self.triangle_indices[:]

    def load(self, path):
        self.clear()

        with open(path) as obj_file:
            for line in obj_file.readlines():
                # reads the file line by line
                data = line.split()

                # every line that begins with a 'v' is a vertex
                if data[0] == 'v':
                    # loads the vertices
                    x, y, z = data[1:4]
                    self.vertices.extend((float(x), float(y), float(z)))

                # every line that begins with an 'f' is a face
                elif data[0] == 'f':
                    # loads the faces
                    for f in data[1:]:
                        if len(data) == 5:
                            # quads
                            # Note: in obj files the first index is 1, so we must subtract one for each
                            # retrieved value
                            vi_1, vi_2, vi_3, vi_4 = data[1:5]
                            self.quad_indices.extend((int(vi_1) - 1, int(vi_2) - 1, int(vi_3) - 1, int(vi_4) - 1))

                        elif len(data) == 4:
                            # triangles
                            # Note: in obj files the first index is 1, so we must subtract one for each
                            # retrieved value
                            vi_1, vi_2, vi_3 = data[1:4]
                            self.triangle_indices.extend((int(vi_1) - 1, int(vi_2) - 1, int(vi_3) - 1))


class Renderer(object):
    """
    Contains the swarm object(s) and cubes and renders everything
    """

    def __init__(self, visualise, swarms):
        """
        :param visualise: bool         whether to render graphics or not
        :param swarms: set{Swarm}   set of swarms
        """
        self.visualise = visualise
        self.swarms = swarms
        self.cubes = set()
        for swarm in swarms:
            self.cubes.add(swarm.cube)

        # (finite) array of colours to colour-code swarms
        # TODO extend as more swarms are needed (preferably algorithmically)
        self.colours = [[60/255, 240/255, 240/255],
                        [240/255, 160/255, 60/255],
                        [240/255, 60/255, 240/255],
                        [180/255, 140,     20/255]]

    def __repr__(self):
        return "TODO - Renderer"

    def add_swarm(self, swarm):
        """
        Allows a swarm to be added in real-time without restarting
        :param swarm: Swarm     new swarm
        """
        self.swarms.append(swarm)
        self.cubes.add(swarm.cube)

    @staticmethod
    def render_axes():
        """
        Draw the XYZ axes
        """
        d = 1000

        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)
        gl.glColor4f(*red)
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v3f', (0, 0, 0,  d, 0, 0)))
        gl.glColor4f(*green)
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v3f', (0, 0, 0,  0, d, 0)))
        gl.glColor4f(*blue)
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v3f', (0, 0, 0,  0, 0, d)))

        # gl.glBegin(gl.gl_LINES)
        # # X
        # gl.glColor(1, 0, 0)
        # gl.glVertex([0, 0, 0])
        # gl.glVertex([d, 0, 0])
        # # Y
        # gl.glColor(0, 1, 0)
        # gl.glVertex([0, 0, 0])
        # gl.glVertex([0, d, 0])
        # # Z
        # gl.glColor(0, 0, 1)
        # gl.glVertex([0, 0, 0])
        # gl.glVertex([0, 0, d])
        # gl.glEnd()

    @staticmethod
    def render_boid(boid, colour):
        """
        Draw a boid
        :param boid:    Boid
        :param colour:  Vector3 colour of boid
        :return:
        """
        # TODO make it cooler than just a line
        gl.glBegin(gl.gl_LINES)
        gl.glColor(colour[0], colour[1], colour[2])
        gl.glVertex(boid.location.get(0), boid.location.get(1), boid.location.get(2))
        if boid.velocity.length() > 0:
            head = boid.location + boid.velocity.normalize() * 2.5
        else:
            head = boid.location
        gl.glVertex(head.get(0), head.get(1), head.get(2))
        gl.glEnd()

    @staticmethod
    def render_com(com):
        """
        TEMP Draw as just a long white boid
        """
        # TODO make it a sphere or something
        gl.glBegin(gl.gl_LINES)
        gl.glColor(0.5, 0.5, 0.5)
        gl.glVertex(com.location.get(0), com.location.get(1), com.location.get(2))
        if com.velocity.length() > 0:
            head = com.location + com.velocity.normalize() * 10
        else:
            head = com.location
        gl.glVertex(head.get(0), head.get(1), head.get(2))
        gl.glEnd()

    def render_swarm(self, swarm, i):
        for boid in swarm.boids:
            self.render_boid(boid, self.colours[i])
        self.render_com(swarm.c_o_m)

    def render(self):
        """
        Render everything
        """
        if self.visualise:
            self.render_axes()
            # TODO:
            # for i, swarm in enumerate(self.swarms):
            #     self.render_swarm(swarm, i)
            # for cube in self.cubes:
            #     CubeView.render(cube)

    def update(self):
        """
        Update all the swarms
        """
        for swarm in self.swarms:
            # TODO temporary way of changing attractor:
            if random.random() < 0.009:
                att = Swarm.rand_point_in_cube(swarm.cube, Vector3)
                swarm.attractor = att
            swarm.update()
