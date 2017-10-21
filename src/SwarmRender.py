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
        """ Draw the bounding box """
        # TODO make more elegant
        ts = CubeView.top_square(cube)
        bs = CubeView.bottom_square(cube)
        # TODO doesn't currently account for angle
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
        :param swarms: set of swarm objects
        """
        self.swarms = swarms
        self.cubes = set()
        for swarm in swarms:
            self.cubes.add(swarm.cube)

    def __repr__(self):
        return "TODO - Renderer"

    def add_swarm(self, swarm):
        self.swarms.append(swarm)

    @staticmethod
    def render_axes():
        """ Draw the XYZ axes """
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
    def render_boid(boid):
        """
        Draw a boid
        """
        # TODO make it cooler than just a line
        GL.glBegin(GL.GL_LINES)
        GL.glColor(boid.colour.x, boid.colour.y, boid.colour.z)
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

    def render_swarm(self, swarm):
        for boid in swarm.boids:
            self.render_boid(boid)
        self.render_com(swarm.c_o_m)

    def render(self):
        """
        Render everything
        """
        self.render_axes()
        for swarm in self.swarms:
            self.render_swarm(swarm)
        for cube in self.cubes:
            CubeView.render(cube)

    def update(self):
        """
        Update all the swarms
        """
        for swarm in self.swarms:
            swarm.update()
