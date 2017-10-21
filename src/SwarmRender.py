import OpenGL.GL as GL

"""
Render the swarm objects
Contains render methods for the displayable classes
"""


class CubeView:
    """
    Contains render method for bounding cube
    """

    @staticmethod
    def top_square(cube):
        """
        :return: Array of points that make up the top of the cube
        """
        return [[cube.x0, cube.y1, cube.z0],
                [cube.x1, cube.y1, cube.z0],
                [cube.x1, cube.y1, cube.z1],
                [cube.x0, cube.y1, cube.z1]]

    @staticmethod
    def bottom_square(cube):
        """
        :return: Array of points that make up the bottom of the cube
        """
        return [[cube.x0, cube.y0, cube.z0],
                [cube.x1, cube.y0, cube.z0],
                [cube.x1, cube.y0, cube.z1],
                [cube.x0, cube.y0, cube.z1]]

    @staticmethod
    def render(cube):
        """
        Draw the bounding box
        """
        # TODO make more elegant
        ts = CubeView.top_square(cube)
        bs = CubeView.bottom_square(cube)
        GL.glColor(0.5, 0.5, 0.5)
        # XY plane, positive Z
        GL.glBegin(GL.GL_LINE_LOOP)
        for point in ts:
            GL.glVertex(point)
        GL.glEnd()
        # XY plane, negative Z
        GL.glBegin(GL.GL_LINE_LOOP)
        for point in bs:
            GL.glVertex(point)
        GL.glEnd()
        # The connecting lines in the Z direction
        GL.glBegin(GL.GL_LINES)
        for (point1, point2) in zip(ts, bs):
            GL.glVertex(point1)
            GL.glVertex(point2)
        GL.glEnd()


class Renderer(object):
    """
    Contains the swarm object(s) and cubes and renders everything
    """

    def __init__(self, swarms):
        """
        :param swarms: set{Swarm}
        """
        self.swarms = swarms
        self.cubes = set()
        for swarm in swarms:
            self.cubes.add(swarm.cube)

        # (finite) array of colours to colour-code swarms
        # TODO extend as more swarms are needed (preferably algorithmically)
        self.colours = [[0.5, 0.0, 0.0],
                        [0.0, 0.5, 0.0],
                        [0.0, 0.0, 0.5]]

    def __repr__(self):
        return "TODO - Renderer"

    def add_swarm(self, swarm):
        """
        Allows a swarm to be added in real-time without restarting
        :param swarm: Swarm     new swarm
        """
        self.swarms.append(swarm)

    @staticmethod
    def render_axes():
        """
        Draw the XYZ axes
        """
        d = 1000
        GL.glBegin(GL.GL_LINES)
        # X
        GL.glColor(1, 0, 0)
        GL.glVertex([0, 0, 0])
        GL.glVertex([d, 0, 0])
        # Y
        GL.glColor(0, 1, 0)
        GL.glVertex([0, 0, 0])
        GL.glVertex([0, d, 0])
        # Z
        GL.glColor(0, 0, 1)
        GL.glVertex([0, 0, 0])
        GL.glVertex([0, 0, d])
        GL.glEnd()

    @staticmethod
    def render_boid(boid, colour):
        """
        Draw a boid
        :param boid:    Boid
        :param colour:  Vector3 colour of boid
        :return:
        """
        # TODO make it cooler than just a line
        GL.glBegin(GL.GL_LINES)
        GL.glColor(colour[0], colour[1], colour[2])
        GL.glVertex(boid.location.x, boid.location.y, boid.location.z)
        if boid.velocity.length() > 0:
            head = boid.location + boid.velocity.normalize() * 2.5
        else:
            head = boid.location
        GL.glVertex(head.x, head.y, head.z)
        GL.glEnd()

    @staticmethod
    def render_com(com):
        """
        TEMP Draw as just a long white boid
        """
        # TODO make it a sphere or something
        GL.glBegin(GL.GL_LINES)
        GL.glColor(0.5, 0.5, 0.5)
        GL.glVertex(com.location.x, com.location.y, com.location.z)
        if com.velocity.length() > 0:
            head = com.location + com.velocity.normalize() * 10
        else:
            head = com.location
        GL.glVertex(head.x, head.y, head.z)
        GL.glEnd()

    def render_swarm(self, swarm, i):
        for boid in swarm.boids:
            self.render_boid(boid, self.colours[i])
        self.render_com(swarm.c_o_m)

    def render(self):
        """
        Render everything
        """
        self.render_axes()
        for i, swarm in enumerate(self.swarms):
            self.render_swarm(swarm, i)
        for cube in self.cubes:
            CubeView.render(cube)

    def update(self):
        """
        Update all the swarms
        """
        for swarm in self.swarms:
            swarm.update()
