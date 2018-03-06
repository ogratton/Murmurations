# adapted from:
# http://www.poketcode.com/pyglet_demos.html
# https://github.com/jjstrydom/pyglet_examples

import pyglet
from pyglet.gl import gl
from pyglet.gl import glu
import random
import os
import math
from copy import deepcopy
from Parameters import DP, SP
from numpy import zeros, float64


from Swarm import normalise
"""
Render the swarm objects
Contains render methods for the displayable classes
"""

# TODO do not allow zooming of total > DIST_BACK
# TODO actually change the whole camera movement controls

# constants
DIST_BACK = 50

# colours
dark_gray = (.75, .75, .75, 1)
white     = (1.0, 1.0, 1.0, 1)
red       = (1.0, 0.0, 0.0, 1)
green     = (0.0, 1.0, 0.0, 1)
blue      = (0.0, 0.0, 1.0, 1)
sky       = (0.3, 0.6, 1.0, 1)
black     = (0.0, 0.0, 0.0, 1)

# models
PYRAMID = 0
SPHERE = 1
BOX = 2


def rand_colour():
    return random.random(), random.random(), random.random(), 1


def invert_colour(colour):
    r, g, b, a = colour
    return 1-r, 1-g, 1-b, a


class World:
    """
    Collection of OBJ models within the larger simulation.
    """

    def __init__(self, swarms, coords, models, background_color=sky):

        # TODO turn off attractor rendering
        self.render_attractors = False

        # original copies of each type of model
        self.models = models

        self.swarms = swarms
        self.cubes = set()
        for swarm in swarms:
            self.cubes.add(swarm.cube)

        # stigmergy setup:
        if swarms[0].boids:  # this line is purely so it is possible to view the attractors on their own if desired
            self.num_leading_boids = len(swarms[0].boids)
            self.num_dims = len(swarms[0].boids[0].location)
            self.leads = [zeros(self.num_dims, dtype=float64)]*self.num_leading_boids

        # make the objects for the cube
        self.boxes = []
        for cube in self.cubes:
            if SP.BOUNDING_SPHERE:
                box_model = deepcopy(self.models[SPHERE])
            else:
                box_model = deepcopy(self.models[BOX])
            box_model.x, box_model.y, box_model.z = list(cube.centre)[:3]
            box_model.color = red  # doesn't matter cos not filled in
            box_model.scale = cube.edge_length/2
            self.boxes.append(box_model)

        self.swarm_models = []
        for swarm in self.swarms:
            colour = rand_colour()
            # boid_size = (swarm.cube.edge_length/2) * 0.02
            # TODO experimenting with fixed sizes
            boid_size = 0.5
            attractor_size = boid_size * 0.2

            boid_models = []
            for boid in swarm.boids:
                boid_model = deepcopy(self.models[PYRAMID])
                boid_model.x, boid_model.y, boid_model.z = list(boid.location)[:3]
                boid_model.color = colour
                boid_model.scale = boid_size
                boid_models.append(boid_model)

            attr_models = []
            if self.render_attractors:
                for attr in swarm.attractors:
                    attractor_model = deepcopy(self.models[BOX])
                    attractor_model.x, attractor_model.y, attractor_model.z = list(attr.location)[:3]
                    attractor_model.color = colour
                    attractor_model.scale = attractor_size
                    attr_models.append(attractor_model)

            self.swarm_models.append((boid_models, attr_models))

        # sets the background color
        gl.glClearColor(*background_color)

        # where the camera starts off:
        [self.x, self.y, self.z] = coords
        # rotation values
        self.rx = self.ry = self.rz = 0
        self.cx, self.cy, self.cz = 0, 0, 0

    def draw(self):
        # clears the screen with the background color
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        gl.glClear(gl.GL_DEPTH_BUFFER_BIT)

        gl.glLoadIdentity()

        # # sets the position for the camera
        gl.glTranslatef(self.x, self.y, self.z)

        # sets the rotation for the camera
        gl.glRotatef(self.rx, 1, 0, 0)
        gl.glRotatef(self.ry, 0, 1, 0)
        gl.glRotatef(self.rz, 0, 0, 1)

        # self.draw_axes()

        for box in self.boxes:
            self.render_model(box, fill=False)

        # TODO won't account for changing number of boids if that is implemented
        for i, (boids_m, atts) in enumerate(self.swarm_models):
            swarm = self.swarms[i]
            for j, boid_m in enumerate(boids_m):

                # experimental: invert colour if feeding
                # if swarm.boids[j].feeding:
                #     boid_m.color = invert_colour(boid_m.color)

                new_loc = list(swarm.boids[j].location)[:3]
                boid_m.x, boid_m.y, boid_m.z = new_loc

                # boid direction based on velocity
                new_vel = list(normalise(swarm.boids[j].velocity[:3]))
                # TODO completely wrong and also stupid but seems to be good enough if you don't look too hard
                # boid_m.rx = math.degrees(math.asin(new_vel[2]/math.sqrt(new_vel[1]**2 + new_vel[2]**2)))
                boid_m.ry = -(90-math.degrees(math.asin(new_vel[0]/math.sqrt(new_vel[2]**2 + new_vel[0]**2))))
                boid_m.rz = -(90-math.degrees(math.asin(new_vel[1]/math.sqrt(new_vel[0]**2 + new_vel[1]**2))))

                self.render_model(boid_m)

            for j, att in enumerate(atts):
                new_att = list(swarm.attractors[j].location)[:3]
                att.x, att.y, att.z = new_att
                self.render_model(att, frame=True)

    @staticmethod
    def draw_axes():
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

    def render_model(self, model, fill=True, frame=True):

        if fill:
            # sets fill mode
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

            # draws the current model
            self.draw_model(model)

        if frame:
            # sets wire-frame mode
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)

            # draws the current model wire-frame
            temp_color = model.color
            model.color = white
            self.draw_model(model)
            model.color = temp_color

    def draw_model(self, model):

        # gl.glLoadIdentity()
        gl.glPushMatrix()

        # sets the color
        gl.glColor4f(*model.color)

        # sets the position
        gl.glTranslatef(model.x - self.cx, model.y - self.cy, model.z - self.cz)

        # sets the rotation
        gl.glRotatef(model.rx, 1, 0, 0)
        gl.glRotatef(model.ry, 0, 1, 0)
        gl.glRotatef(model.rz, 0, 0, 1)

        # sets the scale
        gl.glScalef(model.scale, model.scale, model.scale)

        # draws the quads
        pyglet.graphics.draw_indexed(len(model.vertices) // 3, gl.GL_QUADS, model.quad_indices,
                                     ('v3f', model.vertices))

        # draws the triangles
        pyglet.graphics.draw_indexed(len(model.vertices) // 3, gl.GL_TRIANGLES, model.triangle_indices,
                                     ('v3f', model.vertices))

        gl.glPopMatrix()

    def update(self):
        """ main update loop of the entire simulation is hidden way down here """

        for i, swarm in enumerate(self.swarms):
            # stigmergy!
            if i == 0:
                # LEAD SWARM:
                # get position of every boid as ratios
                for j, boid in enumerate(swarm.boids):
                    self.leads[j] = boid.get_loc_ratios()
            else:
                # FOLLOWER SWARMS:
                # set leading swarm positions as the attractors in followers
                for att in self.leads:
                    swarm.place_attractor(att)
                pass
            swarm.update()


class OBJModel:
    """
    Load an OBJ model from file.
    (Code unchanged from source. See credits file)
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


class Window(pyglet.window.Window):
    """
    Takes care of all the viewing functionality
    """

    def __init__(self, swarms, interps, *args, ** kwargs):
        super().__init__(*args, **kwargs)

        # Load models from files
        self.models = []
        self.model_names = ['pyramid.obj', 'uv_sphere.obj', 'box.obj']
        for name in self.model_names:
            self.models.append(OBJModel((0, 0, 0), path=os.path.join('obj', name)))

        # # current cube to be looking at
        self.cube_index = 0

        self.world = World(swarms, [0, 0, -DIST_BACK], self.models)

        # TODO work out how to display text:
        self.label = pyglet.text.Label('Hello, world',
                                  font_name='Times New Roman',
                                  font_size=36,
                                  x=self.width//2, y=self.height//2,
                                  anchor_x='center', anchor_y='center')

        self.recording = False

        # if SP.RANDOM_SEED != SP.TRUE_RANDOM:
        #     random.seed(SP.RANDOM_SEED)  # for repeatability

        @self.event
        def on_resize(width, height):
            # sets the viewport
            gl.glViewport(0, 0, width, height)

            # sets the projection
            gl.glMatrixMode(gl.GL_PROJECTION)
            gl.glLoadIdentity()
            # gluPerspective(vfov, aspect, near_clipping, far_clipping)
            glu.gluPerspective(90.0, width / height, 0.1, 10000.0)

            # sets the model view
            gl.glMatrixMode(gl.GL_MODELVIEW)
            gl.glEnable(gl.GL_DEPTH_TEST)
            gl.glLoadIdentity()

            return pyglet.event.EVENT_HANDLED

        @self.event
        def on_draw():
            self.world.draw()

        @self.event
        def on_key_press(symbol, modifiers):
            # press the LEFT or RIGHT key to change the current model
            if symbol == pyglet.window.key.RIGHT:
                # next model
                self.cube_index = (self.cube_index + 1) % len(self.world.boxes)

            elif symbol == pyglet.window.key.LEFT:
                # previous model
                self.cube_index = (self.cube_index - 1) % len(self.world.boxes)

            elif symbol == pyglet.window.key.R:
                # toggle recording
                new_status = not self.recording
                for i in interps:
                    i.set_recording(new_status)
                self.recording = new_status

            elif symbol == pyglet.window.key.F:
                # toggle feeding
                SP.FEEDING = not SP.FEEDING

            elif symbol == pyglet.window.key.ESCAPE:
                # finish up any recordings
                for i in interps:
                    i.set_recording(False)
                # exit
                self.close()

        @self.event
        def on_mouse_scroll(x, y, scroll_x, scroll_y):
            # scroll the MOUSE WHEEL to zoom
            self.world.z += scroll_y / 1.0

        @self.event
        def on_mouse_drag(x, y, dx, dy, button, modifiers):
            # press the LEFT MOUSE BUTTON to rotate
            if button == pyglet.window.mouse.LEFT:
                self.world.ry += dx / 5.0
                self.world.rx -= dy / 5.0

            # press the LEFT and RIGHT MOUSE BUTTONS simultaneously to pan
            if button == pyglet.window.mouse.LEFT | pyglet.window.mouse.RIGHT:
                self.world.x += dx / 100.0
                self.world.y += dy / 100.0

        @self.event
        def update(dt):
            self.world.update()
            self.world.cx = self.world.boxes[self.cube_index].x
            self.world.cy = self.world.boxes[self.cube_index].y
            self.world.cz = self.world.boxes[self.cube_index].z

        pyglet.clock.schedule_interval(update, 1/DP.UPDATE_RATE)
