# adapted from:
# http://www.poketcode.com/pyglet_demos.html
# https://github.com/jjstrydom/pyglet_examples

import pyglet
from pyglet.gl import gl
from pyglet.gl import glu
import random
import os
from copy import deepcopy
from parameters import DP, SP

"""
Render the swarm objects
Contains render methods for the displayable classes
"""

# TODO all objects need proper scaling down
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
sky       = (0.5, 0.7, 1.0, 1)


def rand_colour():
    return random.random(), random.random(), random.random(), 1


class World:
    """
    Collection of OBJ models within the larger simulation.
    """

    def __init__(self, swarms, coords, models, background_color=sky):

        # original copies of each type of model
        self.models = models

        self.swarms = swarms
        self.cubes = set()
        for swarm in swarms:
            self.cubes.add(swarm.cube)

        # make the objects for the cube
        self.boxes = []
        for cube in self.cubes:
            box_model = deepcopy(self.models[0])
            box_model.x, box_model.y, box_model.z = list(cube.centre)[:3]  # TODO atm just take the first 3 dims
            box_model.color = red  # doesn't matter cos not filled in
            box_model.scale = cube.edge_length/2
            self.boxes.append(box_model)

        # TODO make this a dict so i can use it nicer
        self.swarm_colours = []
        self.swarm_models = []
        for swarm in self.swarms:
            self.swarm_colours.append(rand_colour())
            model_size = (swarm.cube.edge_length/2) * 0.02

            boid_models = []
            for boid in swarm.boids:
                boid_model = deepcopy(self.models[0])
                boid_model.x, boid_model.y, boid_model.z = list(boid.location)[:3]  # TODO !!
                boid_model.color = self.swarm_colours[-1]  # TODO update after dict switch
                boid_model.scale = model_size
                boid_models.append(boid_model)

            attractor_model = deepcopy(self.models[1])
            attractor_model.x, attractor_model.y, attractor_model.z = list(swarm.attractor)[:3]  # TODO !!
            attractor_model.color = blue
            attractor_model.scale = model_size
            self.swarm_models.append((boid_models, attractor_model))

        # sets the background color
        gl.glClearColor(*background_color)

        # where the camera starts off:
        [self.x, self.y, self.z] = coords
        # rotation values
        self.rx = self.ry = self.rz = 0
        # TODO focal point?
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

        self.draw_axes()

        # for model in self.models:
        #     self.render_model(model)

        for box in self.boxes:
            self.render_model(box, False)

        # TODO this may be very slow
        for i, (boids_m, att) in enumerate(self.swarm_models):
            swarm = self.swarms[i]
            for j, boid_m in enumerate(boids_m):
                new_loc = list(swarm.boids[j].location)[:3]
                boid_m.x, boid_m.y, boid_m.z = new_loc
                self.render_model(boid_m, True)
            new_att = list(swarm.attractor)[:3]
            att.x, att.y, att.z = new_att
            self.render_model(att, True)

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

    def render_model(self, model, fill):

        if fill:
            # sets fill mode
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

            # draws the current model
            self.draw_model(model)

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

    def update(self, dt):
        # print(dt)

        for swarm in self.swarms:
            swarm.update()


class OBJModel:
    """
    Load an OBJ model from file.
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

    def __init__(self, swarms, *args, ** kwargs):
        super().__init__(*args, **kwargs)

        # Load models from files
        self.models = []
        self.model_names = ['box.obj', 'uv_sphere.obj', 'monkey.obj']
        for name in self.model_names:
            self.models.append(OBJModel((0, 0, 0), path=os.path.join('obj', name)))

        # # current cube to be looking at
        self.cube_index = 0

        self.world = World(swarms, [0, 0, -DIST_BACK], self.models)

        if SP.RANDOM_SEED != SP.TRUE_RANDOM:
            random.seed(SP.RANDOM_SEED)  # for repeatability

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

            elif symbol == pyglet.window.key.ESCAPE:
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
            self.world.update(dt)
            self.world.cx = self.world.boxes[self.cube_index].x
            self.world.cy = self.world.boxes[self.cube_index].y
            self.world.cz = self.world.boxes[self.cube_index].z

        pyglet.clock.schedule_interval(update, 1/DP.UPDATE_RATE)
