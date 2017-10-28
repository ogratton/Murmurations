# Adapted from code by Tom Marble
# https://github.com/tmarble/pyboids/blob/master/boids.py

import random
from vectors import Vector3

"""
TODO:
- add attractors
- fiddle with values in rules
"""

random.seed(72)  # for repeatability


def random_range(lower=0.0, upper=1.0):
    """
    :return: a random number between lower and upper
    """
    return lower + (random.random() * (upper - lower))


def random_vector(cls, lower=0.0, upper=1.0):
    """
    :param cls: vector class to produce
    :return: a vector with random elements between lower and upper
    """
    data = [random_range(lower, upper) for _ in range(cls.n)]
    return cls(data)

def rand_point_in_cube(cube, cls):
    """
    done with gauss for n dims rather than uniform for 3
    :param cube: Cube object
    :param cls: vector class to produce
    :return:
    """
    edge = cube.edge_length
    sd = edge/7.5

    points = []

    for i in range(cls.n):
        while True:
            p = random.gauss(edge/2, sd)
            if max(0, min(p, edge)) not in [0, edge]:
                break
        points.append(p + cube.v_min.get(i))

    return cls(points)


class Cube(object):
    """
    Bounding box for swarm
    """

    def __init__(self, v_min, edge_length):
        """
        Set up a bounding box that constrains the swarm(s)
        :param v_min:       Vector3     the minimum vertex of the cube (closest to origin)
        :param edge_length: float       the length of each edge (currently always a perfect cube)
        """

        self.v_min = v_min
        self.edge_length = edge_length
        self.centre = Vector3([v_min.get(0) + 0.5 * edge_length,
                              v_min.get(1) + 0.5 * edge_length,
                              v_min.get(2) + 0.5 * edge_length])

        # used for rendering
        self.x0 = v_min.get(0)
        self.y0 = v_min.get(1)
        self.z0 = v_min.get(2)
        self.x1 = self.x0 + edge_length
        self.y1 = self.y0 + edge_length
        self.z1 = self.z0 + edge_length

    def __repr__(self):
        return "Cube from {0} with edge length {1}".format(self.v_min, self.edge_length)


class Rule(object):
    """
    Template for rules of flocking
    """

    def __init__(self):
        """
        Initialise aggregators change and num
        Set potency of rule ('neighbourhood')
        """
        self.change = Vector3()    # velocity correction
        self.num = 0               # number of participants
        self.neighbourhood = 5.0   # number of boids to account for around one boid

    def accumulate(self, boid, other, distance):
        """
        Save any corrections based on other boid to self.change
        """
        pass

    def add_adjustment(self, boid):
        """
        Add the accumulated self.change to boid.adjustment
        """
        pass


class Cohesion(Rule):
    """ Rule 1: Boids try to fly towards the centre of mass of neighbouring boids. """

    def __init__(self):
        super().__init__()
        self.neighbourhood = 25.0

    def accumulate(self, boid, other, distance):
        if other != boid:
            self.change = self.change + other.location
            self.num += 1

    def add_adjustment(self, boid):
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
        if other != boid:
            self.change = self.change + other.velocity
            self.num += 1

    def add_adjustment(self, boid):
        if self.num > 0:
            group_velocity = self.change / self.num
            self.change = (group_velocity - boid.velocity) * 0.03
        boid.adjustment = boid.adjustment + self.change


class Separation(Rule):
    """ Rule 3: Boids try to keep a small distance away from other objects (including other boids). """

    def __init__(self):
        super().__init__()

    def accumulate(self, boid, other, distance):
        if other != boid:
            separation = boid.location - other.location
            if separation.length() > 0:
                self.change = self.change + (separation.normalize() / distance)
            self.num += 1

    def add_adjustment(self, boid):
        if self.change.length() > 0:
            group_separation = self.change / self.num
            self.change = (group_separation - boid.velocity) * 0.01
        boid.adjustment = boid.adjustment + self.change


class Attraction:
    """ Bonus Rule: Fly towards the attractor """

    @staticmethod
    def add_adjustment(boid):
        to_attractor = boid.attractor - boid.location
        change = to_attractor * 0.005  # TODO experimental value
        boid.adjustment = boid.adjustment + change


class Constraint:
    """ Bonus Rule: Boids must stay within the bounding cube. """

    @staticmethod
    def add_adjustment(boid):
        change = Vector3()
        if boid.turning:
            direction = boid.cube.centre - boid.location
            change = direction * 0.001  # TODO experimental value
        boid.adjustment = boid.adjustment + change


class Boid(object):
    """
    A single swarm agent
    """

    def __init__(self, cube, attractor):
        """
        Make a baby boid
        :param cube: Cube   bounding box for this boid
        """
        self.cube = cube
        self.attractor = attractor

        # doesn't seem to matter that much where you start
        # even if it's outside the cube
        # either start at centre or at a random location:
        # self.location = cube.centre
        self.location = rand_point_in_cube(cube, Vector3)
        # self.location = Vector3()

        self.velocity = random_vector(Vector3, -1.0, 1.0)  # vx vy vz
        self.adjustment = Vector3()  # to accumulate corrections
        self.turning = False

    def __repr__(self):
        return "Boid - pos:{0}, vel:{1}".format(self.location, self.velocity)

    def calc_v(self, all_boids):
        """
        Calculate velocity for next tick by applying the three basic swarming rules
        """
        # Apply the rules to each of the boids
        # TODO flocks use alignment, swarms do not
        flock = True
        rules = [Cohesion(), Separation()]
        if flock:
            rules.append(Alignment())
        # bonus rules don't need the accumulate stage
        bonus_rules = [Constraint(), Attraction()]

        for boid in all_boids:
            distance = self.location.distance_to(boid.location)
            for rule in rules:
                if distance < rule.neighbourhood:
                    rule.accumulate(self, boid, distance)
        self.adjustment = Vector3()  # reset adjustment vector
        for rule in rules:  # save corrections to the adjustment
            rule.add_adjustment(self)
        for rule in bonus_rules:
            rule.add_adjustment(self)

    def limit_speed(self, max_speed):
        """
        Ensure the speed does not exceed max_speed
        :param max_speed: float
        """
        if self.velocity.length() > max_speed:
            self.velocity = self.velocity.normalize() * max_speed

    def update(self):
        """
        Move to new position using calculated velocity
        """
        velocity = self.velocity + self.adjustment
        # Add a constant velocity in whatever direction
        # they are moving so they don't ever stop.
        # Now that we have attractors, this is unnecessary
        # if velocity.length() > 0:
        #     velocity = velocity + (velocity.normalize() * random_range(0.0, 0.007))

        self.velocity = velocity
        self.limit_speed(1.0)
        self.location = self.location + self.velocity
        # bool to keep the boid in the box (technically this describes a sphere)
        # TODO experimental values
        self.turning = (self.location.distance_to(self.cube.centre) >= self.cube.edge_length*0.80/2)


class Attractor(object):
    """
    Attracts boid towards it
    """
    def __init__(self, location):
        self.location = location

    def set_pos(self, new_l):
        self.location = new_l


class CentOfMass(object):
    """
    The centre of mass of a swarm
    """
    def __init__(self, location, velocity, v_min):
        """
        Set up an initial (probably wrong) centre of mass object
        :param location: Vector3
        :param velocity: Vector3
        :param v_min:    min vertex of bounding box
        """
        self.location = location
        self.velocity = velocity
        self.v_min = v_min

    def __repr__(self):
        return "Centre of Mass - pos:{0}, vel:{1}".format(self.location, self.velocity)

    def set(self, location, velocity):
        """
        Set the location and velocity of the c.o.m
        :param location: Vector3
        :param velocity: Vector3
        """
        self.location = location
        self.velocity = velocity

    def get_location(self):
        """
        USE THIS RATHER THAN ACCESSING location
        :return: Location relative to v_min (i.e v_min is origin)
        """
        return self.location - self.v_min


class Swarm(object):
    """
    A swarm of boids
    """

    def __init__(self, num_boids, cube, attractor=None):
        """
        Set up a swarm
        :param num_boids: int   number of boids in the swarm
        :param cube:      Cube  bounding box of swarm (and its boids)
        """
        super().__init__()
        self.num_boids = num_boids
        self.boids = []
        self.cube = cube
        if attractor is None:
            self.attractor = cube.centre
        else:
            self.attractor = attractor
        for _ in range(num_boids):
            self.boids.append(Boid(cube, self.attractor))
        self.c_o_m = CentOfMass(cube.centre, Vector3(), cube.v_min)

    def __repr__(self):
        return "Swarm of {0} boids in cube with min vertex {1}".format(self.num_boids, self.cube.v_min)

    def update(self):
        """
        Update every boid in the swarm and calculate the swarm's centre of mass
        """
        p_acc = Vector3()
        v_acc = Vector3()
        for boid in self.boids:
            boid.calc_v(self.boids)
            boid.attractor = self.attractor
        for boid in self.boids:  # TODO is this line necessary? (calc all v first or one at a time?)
            boid.update()
            # TODO may need to do clustering and calculate the centre of the densest point
            p_acc = p_acc + boid.location
            v_acc = v_acc + boid.velocity
        self.c_o_m.set(p_acc / self.num_boids, v_acc / self.num_boids)

    def get_COM(self):
        """
        :return: the centre of mass of the swarm relative, but treating v_min as the origin
        """
        com = self.c_o_m
        return com
