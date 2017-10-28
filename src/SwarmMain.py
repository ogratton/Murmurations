from datetime import datetime  # temp

import Swarm
import SwarmRender

import math
import pygame
import pygame.locals as pyg
from vectors import Vector3
import OpenGL.GL as GL
import OpenGL.GLU as GLU

"""
Main method for running the swarm simulation

NOW USELESS FOR AUDIO
Use Interpreter for audio and this for visualisation until I do the graphics in pyglet
"""


def main():
    # TODO I don't get most of this, it's just boring setup code. Mostly Tom Marble:
    # set up display window
    title = "Swarm Music Demo v.-1000"
    window_size = 700
    xy_ratio = 1  # x side / y side
    cam_rotation = math.radians(0.1)
    cam_angle = 0  # keep track of how far we have rotated
    rotation_delay = 0

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

    renderer = SwarmRender.Renderer(True, swarms)

    # CAMERA/GL STUFF
    cam_r = 2 * cube.edge_length  # distance of camera from cube_centre
    focal_point = cube.centre

    pygame.init()
    pygame.display.set_caption(title, title)
    pygame.display.set_mode((window_size, window_size), pyg.OPENGL | pyg.DOUBLEBUF)
    GL.glEnable(GL.GL_DEPTH_TEST)
    GL.glClearColor(0, 0, 0, 0)
    # set up the camera
    GL.glMatrixMode(GL.GL_PROJECTION)
    GL.glLoadIdentity()
    GLU.gluPerspective(edge_length * 2, xy_ratio, 1.0, (6 * edge_length) + 10)  # setup lens
    GL.glMatrixMode(GL.GL_MODELVIEW)
    GL.glLoadIdentity()
    # look at the middle of the cube
    cam_pos = Vector3([0.5 * edge_length, 0.5 * edge_length, cam_r])
    GLU.gluLookAt(cam_pos.get(0), cam_pos.get(1), cam_pos.get(2),
                  focal_point.get(0), focal_point.get(1), focal_point.get(2),
                  0.0, 1.0, 0.0)
    # diameter of rasterised points
    GL.glPointSize(3.0)

    counter = 0
    time = datetime.now()
    while True:
        event = pygame.event.poll()
        if event.type == pyg.QUIT or (event.type == pyg.KEYDOWN and
            (event.key == pyg.K_ESCAPE or event.key == pyg.K_q)):
            print("Shutting down")
            break

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        renderer.render()

        pygame.display.flip()  # update screen
        if rotation_delay > 0:
            pygame.time.wait(rotation_delay)

        renderer.update()

        if counter % 100 == 0:
            print(datetime.now() - time)
            time = datetime.now()
        counter += 1

if __name__ == '__main__':
    main()
