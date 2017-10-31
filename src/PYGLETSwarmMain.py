from datetime import datetime  # temp

import Swarm
import PYGLETSwarmRender
import pyglet
from pyglet.gl import gl
from pyglet.gl import glu
import os
import copy

import math

from vectors import Vector3

# TODO IN THE MIDDLE OF TRANSITIONING TO PYGLET SO THIS IS ALL SHIT

"""
Main method for running the swarm simulation

"""


class Window(pyglet.window.Window):
    """
    Takes care of all the viewing functionality
    """

    def __init__(self, *args, ** kwargs):
        super().__init__(*args, **kwargs)

        # pre-loaded models
        self.model_names = ['box.obj', 'uv_sphere.obj', 'monkey.obj']
        self.models = []

        for name in self.model_names:
            self.models.append(PYGLETSwarmRender.OBJModel((0, 0, 0),
                                                          color=PYGLETSwarmRender.dark_gray,
                                                          path=os.path.join('obj', name)))

        # # current model
        self.model_index = 0
        # self.current_model = self.models[self.model_index]

        sphere1 = copy.deepcopy(self.models[0])
        sphere2 = copy.deepcopy(self.models[2])
        sphere3 = copy.deepcopy(self.models[1])

        sphere1.x, sphere1.y, sphere1.z = [-1, 2, -3.5]
        sphere1.color = (1, 0, 0, 1)
        sphere1.scale = 0.5
        sphere2.x, sphere2.y, sphere2.z = [1, 2, -3.5]
        sphere2.color = (0, 0, 1, 1)

        sphere3.x, sphere3.y, sphere3.z = [2, 4, 2]
        sphere3.color = (1, 1, 0, 1)
        sphere3.scale = 0.1

        self.world = World([0, 0, -5])
        self.world.models.append(sphere1)
        self.world.models.append(sphere2)
        self.world.models.append(sphere3)

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
                self.model_index = (self.model_index + 1) % len(self.world.models)

            elif symbol == pyglet.window.key.LEFT:
                # previous model
                self.model_index = (self.model_index - 1) % len(self.world.models)

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
            self.world.cx = self.world.models[self.model_index].x
            self.world.cy = self.world.models[self.model_index].y
            self.world.cz = self.world.models[self.model_index].z

        pyglet.clock.schedule_interval(update, 1/PYGLETSwarmRender.UPDATE_RATE)


def main():

    # DEFINE BOUNDING BOX(ES)
    cube_min = Vector3([10, -5, 7])  # cube min vertex
    edge_length = 50.0

    cube = Swarm.Cube(cube_min, edge_length)

    # MAKE SWARM OBJECTS
    # swarm, channel (starting from 1), instrument code
    swarm_data = [
                    (Swarm.Swarm(7, cube), 1, 56),
                    (Swarm.Swarm(7, cube), 2, 1),
                    (Swarm.Swarm(7, cube), 3, 26),
                    (Swarm.Swarm(7, cube), 9, 0)
    ]
    swarms = list(map(lambda x: x[0], swarm_data))

    renderer = PYGLETSwarmRender.Renderer(True, swarms)

    config = pyglet.gl.Config(sample_buffers=1, samples=4)

    # creates the window and sets its properties
    window = Window(config=config, width=400, height=400, caption='OBJ Viewer', resizable=True)

    # starts the application
    pyglet.app.run()


if __name__ == '__main__':
    main()
