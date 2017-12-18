# Adapted from code by Tom Marble
# https://github.com/tmarble/pyboids/blob/master/boids.py

import random
from numpy import r_
from numpy.linalg import norm
from parameters import SP
from heapq import (heappush, heappop)
from math import (cos, sin, pi)

def random_range(lower=0.0, upper=1.0):
    """
    :return: a random number between lower and upper
    """
    return lower + (random.random() * (upper - lower))


def random_vector(dims, lower=0.0, upper=1.0):
    """
    :param dims: number of dimensions of resultant vector
    :param lower: float lower bound for random_range
    :param upper: float upper bound for random_range
    :return: a vector with <dims> random elements between lower and upper
    """
    data = [random_range(lower, upper) for _ in range(dims)]
    return r_[data]


def rand_point_in_cube(cube, dims):
    """
    done with gauss for n dims
    :param cube: Cube object
    :param dims: number of dimensions
    :return:
    """
    edge = cube.edge_length
    sd = edge/SP.RAND_POINT_SD

    points = []

    for i in range(dims):
        p = 0
        while True:
            p = random.gauss(edge/2, sd)
            if max(0, min(p, edge)) not in [0, edge]:
                break
        points.append(p + cube.v_min[i])

    return r_[points]


def normalise(vector):
    """
    Normalise a numpy r_ vector
    :param vector: r_
    :return: r_ normalised
    """
    return vector/norm(vector)


class Cube(object):
    """
    Bounding box for swarm
    """

    def __init__(self, v_min, edge_length):
        """
        Set up a bounding box that constrains the swarm(s)
        :param v_min:       r_      the minimum vertex of the cube (closest to origin)
        :param edge_length: float   the length of each edge (currently always a perfect cube)
        """

        self.v_min = v_min
        self.edge_length = edge_length
        self.centre = r_[v_min[0] + 0.5 * edge_length,
                         v_min[1] + 0.5 * edge_length,
                         v_min[2] + 0.5 * edge_length]

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
        self.change = r_[0., 0., 0.]    # velocity correction
        self.num = 0                    # number of participants
        # TODO: this should be the NUMBER of boids it accounts for, not a distance
        self.neighbourhood = 0.5        # sphere of view of boid as ratio of cube edge length (overwritten later)

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
        self.neighbourhood = SP.COHESION_NEIGHBOURHOOD

    def accumulate(self, boid, other, distance):
        if other != boid:
            self.change += other.location
            self.num += 1

    def add_adjustment(self, boid):
        if self.num > 0:
            centroid = self.change / self.num
            desired = centroid - boid.location
            self.change = (desired - boid.velocity) * SP.COHESION_MULTIPLIER
        boid.adjustment += self.change


class Alignment(Rule):
    """ Rule 2: Boids try to match velocity with near boids. """

    def __init__(self):
        super().__init__()
        self.neighbourhood = SP.ALIGNMENT_NEIGHBOURHOOD

    def accumulate(self, boid, other, distance):
        if other != boid:
            self.change += other.velocity
            self.num += 1

    def add_adjustment(self, boid):
        if self.num > 0:
            group_velocity = self.change / self.num
            self.change = (group_velocity - boid.velocity) * SP.ALIGNMENT_MULTIPLIER
        boid.adjustment += self.change


class Separation(Rule):
    """ Rule 3: Boids try to keep a small distance away from other objects (including other boids). """

    def __init__(self):
        super().__init__()
        self.neighbourhood = SP.SEPARATION_NEIGHBOURHOOD

    def accumulate(self, boid, other, distance):
        # calc vector from boid2 to boid1 (NOT other way round as we want repulsion)
        repulsion = boid.location - other.location
        if distance > 0:
            # this normalises the repulsion vector and makes closer boids repel more
            self.change += repulsion / distance**2  # makes it an inverse square rule
        self.num += 1

    def add_adjustment(self, boid):
        # here norm is vector magnitude
        if norm(self.change) > 0:
            group_separation = self.change / self.num
            self.change = (group_separation - boid.velocity) * SP.SEPARATION_MULTIPLIER
        boid.adjustment += self.change


class Attraction:
    """ Bonus Rule: Fly towards the attractor(s) """

    @staticmethod
    def add_adjustment(boid):
        # priority queue of (distance, change)
        dist_mat = []

        for attr in boid.attractors:
            to_attractor = attr.location - boid.location
            dist = norm(to_attractor)
            # 1/dist makes attraction stronger for closer attractors
            change = (to_attractor - boid.velocity) * SP.ATTRACTION_MULTIPLIER * (1/dist)
            heappush(dist_mat, (dist, list(change)))  # needs to be a list as r_ is 'ambiguous'

        # only feel the pull of the nearest <x> attractors
        attention_span = min(SP.ATTRACTORS_NOTICED, len(boid.attractors))
        for _ in range(attention_span):
            boid.adjustment += heappop(dist_mat)[1]


class Constraint:
    """ Bonus Rule: Boids must stay within the bounding cube. """

    @staticmethod
    def add_adjustment(boid):
        change = r_[0., 0., 0.]
        if boid.turning:
            direction = boid.cube.centre - boid.location
            change = direction * SP.CONSTRAINT_MULTIPLIER
        boid.adjustment = boid.adjustment + change


class Boid(object):
    """
    A single swarm agent
    """

    def __init__(self, cube, attractors):
        """
        Make a baby boid
        :param cube: Cube   bounding box for this boid
        :param attractors: [Attractor]
        """
        self.cube = cube
        self.attractors = attractors

        # doesn't matter that much where you start
        self.location = rand_point_in_cube(cube, 3)

        self.velocity = random_vector(3, -1.0, 1.0)  # vx vy vz
        self.adjustment = r_[0., 0., 0.]  # to accumulate corrections from rules
        self.turning = False

    def __repr__(self):
        return "Boid - pos:{0}, vel:{1}".format(self.location, self.velocity)

    def calc_v(self, all_boids):
        """
        Calculate velocity for next tick by applying the swarming rules
        """
        # Apply the rules to each of the boids
        # flocks use alignment, swarms do not
        flock = SP.IS_FLOCK
        rules = [Separation(), Cohesion()]
        if flock:
            rules.append(Alignment())
        # bonus rules don't need the accumulate stage
        bonus_rules = [Constraint(), Attraction()]

        # TODO this makes the swarm O(n^2) instead of linear. Maybe find a better data structure than list
        # TODO turns out this is the bottleneck of the whole program...
        # in actual bird flocks, it is suggested they look at the nearest (say) 7 birds regardless of metric distance
        # this is topological distance.
        for boid in all_boids:
            distance = norm(self.location-boid.location)
            for rule in rules:
                if distance < rule.neighbourhood*self.cube.edge_length:
                    rule.accumulate(self, boid, distance)
        self.adjustment = r_[0., 0., 0.]  # reset adjustment vector
        for rule in rules:  # save corrections to the adjustment
            rule.add_adjustment(self)
        for rule in bonus_rules:
            rule.add_adjustment(self)

    def limit_speed(self, max_speed):
        """
        Ensure the speed does not exceed max_speed
        :param max_speed: float
        """
        if norm(self.velocity) > max_speed:
            self.velocity = normalise(self.velocity) * max_speed

    def get_location(self):
        """
        :return: position relative to cube (with v_min as origin)
        """
        return self.location - self.cube.v_min

    def update(self):
        """
        Move to new position using calculated velocity
        """
        velocity = self.velocity + self.adjustment
        # Add a constant velocity in whatever direction
        # they are moving so they don't ever stop.
        # Now that we have attractors, this is unnecessary
        if norm(velocity) > 0:
            velocity += (normalise(velocity) * random_range(0.0, SP.MOTION_CONSTANT))

        self.velocity = velocity
        self.limit_speed(SP.MAX_SPEED)
        self.location = self.location + self.velocity

        if SP.BOUNDING_SPHERE:
            self.turning = (norm(self.location-self.cube.centre) >= self.cube.edge_length*SP.TURNING_RATIO/2)
        else:
            self.turning = False
            for dim in range(len(self.location)):
                self.turning = self.turning or norm(self.location[dim]-self.cube.centre[dim]) >= self.cube.edge_length*SP.TURNING_RATIO/2


class Attractor(object):
    """
    Attracts boid towards it
    """
    def __init__(self, location, cube):
        self.location = location
        # TODO experimental values used here
        self.cube = cube
        self.t = random.random()  # start a random way along
        self.step = random.randrange(50, 200)/100000  # at a random speed too

        # make a random parametric path
        # in this 3d example, the dimension that we leave "pi" out of varies less
        # so if x is dynamic and x_f is simply cos(4t) then it will move slower and have
        # less dynamic interest
        a, b, c = random.randint(1, 8), random.randint(1, 8), random.randint(1, 5)
        self.x_f = lambda t: cos(a * t)
        self.y_f = lambda t: sin(b * pi * t)
        self.z_f = lambda t: sin(c * pi * t)

    def set_pos(self, new_l):
        self.location = new_l

    def step_path_equation(self):
        # TODO set path in n dimensions
        # parametric equations:
        x = self.x_f(self.t)
        y = self.y_f(self.t)
        z = self.z_f(self.t)
        self.t += self.step
        new_point = r_[x, y, z]*0.4*self.cube.edge_length + self.cube.centre
        self.set_pos(new_point)


class CentOfMass(object):
    """
    The centre of mass of a swarm
    """
    def __init__(self, location, velocity, v_min):
        """
        Set up an initial (probably wrong) centre of mass object
        :param location: r_
        :param velocity: r_
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
        :param location: r_
        :param velocity: r_
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
    def __init__(self, num_boids, cube, num_attractors=1):
        """
        Set up a swarm
        :param num_boids: int   number of boids in the swarm
        :param cube:      Cube  bounding box of swarm (and its boids)
        """
        super().__init__()
        self.num_boids = num_boids
        self.boids = []
        self.cube = cube
        self.attractors = []
        self.att_index = 0  # for midi-input mode
        for _ in range(num_attractors):
            self.attractors.append(Attractor(rand_point_in_cube(self.cube, 3), cube))  # cube.centre

        for _ in range(num_boids):
            self.boids.append(Boid(cube, self.attractors))
        self.c_o_m = CentOfMass(cube.centre, r_[0., 0., 0.], cube.v_min)

        # TODO this doesn't actually work here
        if SP.RANDOM_SEED != SP.TRUE_RANDOM:
            random.seed(SP.RANDOM_SEED)  # for repeatability

    def __repr__(self):
        return "Swarm of {0} boids in cube with min vertex {1}".format(self.num_boids, self.cube.v_min)

    def midi_to_attractor(self, ratios):
        """
        Convert a MIDI message to an attractor
        :param ratios: ratio of how far along to place attractor on each axis
        """
        cube = self.cube
        v_min = cube.v_min
        edge = cube.edge_length
        pos = []
        for i, dim in enumerate(ratios):
            pos.append(v_min[i] + dim*edge)
        print(pos)
        self.attractors[self.att_index].location = r_[pos]
        self.att_index = (self.att_index + 1) % len(self.attractors)
        return

    def update(self):
        """
        Update every boid in the swarm and calculate the swarm's centre of mass
        """
        # position and velocity accumulators
        p_acc = r_[0., 0., 0.]
        v_acc = r_[0., 0., 0.]
        for boid in self.boids:
            boid.calc_v(self.boids)
            boid.attractors = self.attractors
        for boid in self.boids:  # TODO is this line necessary? (calc all v first or one at a time?)
            boid.update()
            p_acc = p_acc + boid.location
            v_acc = v_acc + boid.velocity
        # calculate the centre of mass
        self.c_o_m.set(p_acc / self.num_boids, v_acc / self.num_boids)
        # update attractors
        if SP.ATTRACTOR_MODE == 0:
            for i, attr in enumerate(self.attractors):
                if random.random() < SP.RAND_ATTRACTOR_CHANGE:
                    att = Attractor(rand_point_in_cube(self.cube, 3), self.cube)
                    self.attractors[i] = att
        elif SP.ATTRACTOR_MODE == 1:
            for i, attr in enumerate(self.attractors):
                attr.step_path_equation()
        elif SP.ATTRACTOR_MODE == 2:
            pass  # this is handled by the callback function midi_to_attractor
        else:
            print("Unimplemented ATTRACTOR_MODE value: {0}".format(SP.ATTRACTOR_MODE))
            SP.ATTRACTOR_MODE = 0


    def get_COM(self):
        """
        WARNING: MUST USE com.get_location()
        :return: the centre of mass of the swarm
        """
        # TODO make this foolproof
        com = self.c_o_m
        return com
