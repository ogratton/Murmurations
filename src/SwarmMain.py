import Sound
import Swarm
import SwarmRender
import Interpreter

import math
import pygame
import pygame.locals as pyg
from pygame.math import Vector3
import OpenGL.GL as GL
import OpenGL.GLU as GLU

"""
Main method for running the swarm simulation
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
    cube_min = Vector3(10, -5, 7)  # cube min vertex
    edge_length = 50.0

    cube = Swarm.Cube(cube_min, edge_length)

    # MAKE SWARM OBJECTS
    swarm = Swarm.Swarm(7, cube)
    swarm2 = Swarm.Swarm(7, cube)
    # swarm3 = Swarm.Swarm(7, cube)

    swarm_data = [(swarm, 1, 56), (swarm2, 2, 67)]  # , (swarm3, 3, 57)]
    swarms = list(map(lambda x: x[0], swarm_data))

    renderer = SwarmRender.Renderer(True, swarms)

    # START AUDIO THREADS
    threads_and_players = []
    for i, (swarm, port, instrument) in enumerate(swarm_data):
        player = Sound.Player(port, instrument)
        thread = Interpreter.Listener(i, "listener " + str(i), swarm, player)
        threads_and_players.append((thread, player))
        thread.start()
        print("Started sound thread " + str(i))

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
    cam_pos = Vector3(0.5 * edge_length, 0.5 * edge_length, cam_r)
    GLU.gluLookAt(cam_pos.x, cam_pos.y, cam_pos.z, focal_point.x, focal_point.y, focal_point.z, 0.0, 1.0, 0.0)
    # diameter of rasterised points
    GL.glPointSize(3.0)

    while True:
        event = pygame.event.poll()
        if event.type == pyg.QUIT or (event.type == pyg.KEYDOWN and
            (event.key == pyg.K_ESCAPE or event.key == pyg.K_q)):
            # CLEANUP
            for thread, player in threads_and_players:
                thread.stop()
                # del player
            break

        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        renderer.render()

        # rotate the camera around the focal point
        # METHOD 1 (rotates around origin only)
        #GL.glRotatef(math.degrees(cam_rotation), 0, 1, 0)  # orbit camera around by angle

        # METHOD 2 (broken)
        # cam_pos.x = cam_r * math.sin(cam_angle) + (0.5 * edge_length)  # TODO
        # cam_pos.z = cam_r * math.cos(cam_angle) + (0.5 * edge_length)  # TODO
        # GLU.gluLookAt(cam_pos.x, cam_pos.y, cam_pos.z, focal_point.x, focal_point.y, focal_point.z, 0.0, 1.0, 0.0)
        # cam_angle += cam_rotation
        # #print(cam_pos)
        # #cam_angle %= 2 * math.pi

        pygame.display.flip()  # update screen
        if rotation_delay > 0:
            pygame.time.wait(rotation_delay)
        renderer.update()

if __name__ == '__main__':
    main()
