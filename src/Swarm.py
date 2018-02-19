# Adapted from code by Tom Marble
# https://github.com/tmarble/pyboids/blob/master/boids.py

import random
from numpy import array, zeros, float64, nditer, append
from numpy.linalg import norm
from Parameters import SP
from heapq import (heappush, heappop)
from math import (cos, sin, pi)

# TODO TEMP
# random.seed(SP.RANDOM_SEED)

DIMS = 5  # for when dimensions must be hardcoded

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
    return array(data)


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

    return array(points, dtype=float64)


def normalise(vector):
    """
    Normalise a numpy array vector
    :param vector: array
    :return: array normalised
    """
    return vector/norm(vector)


class Cube(object):
    """
    Bounding box for swarm
    """

    def __init__(self, v_min, edge_length):
        """
        Set up a bounding box that constrains the swarm(s)
        :param v_min:       array   the minimum vertex of the cube (closest to origin)
        :param edge_length: float   the length of each edge (currently always a perfect cube)
        """

        self.v_min = v_min
        self.edge_length = edge_length
        pos = [j + 0.5 * edge_length for j in v_min]
        self.centre = array(pos, dtype=float64)

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
        self.change = zeros(DIMS, dtype=float64)    # velocity correction
        self.num = 0                    # number of participants
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

        # TODO EXPERIMENTAL: ATTRACTION_MULTIPLIER is a function of its position in the nth dimension
        # this means that when the boid will be attracted to the attractor at the top of d1, and repulsed at the base
        att_mul = SP.ATTRACTION_MULTIPLIER
        n = 4  # which dimension to use
        proportion = boid.get_loc_ratios()[n]
        if proportion < 0.3:
            att_mul = -SP.ATTRACTION_MULTIPLIER

        for attr in boid.attractors:
            to_attractor = attr.location - boid.location
            dist = norm(to_attractor)
            boid.feeding = dist < SP.FEED_DIST
            # 1/dist makes attraction stronger for closer attractors
            change = (to_attractor - boid.velocity) * att_mul * (1/dist)
            heappush(dist_mat, (dist, list(change)))  # needs to be a list as ndarray is 'ambiguous'

        # only feel the pull of the nearest <x> attractors
        attention_span = min(SP.ATTRACTORS_NOTICED, len(boid.attractors))
        for _ in range(attention_span):
            boid.adjustment += heappop(dist_mat)[1]


class Constraint:
    """ Bonus Rule: Boids must stay within the bounding cube. """

    @staticmethod
    def add_adjustment(boid):
        change = zeros(DIMS, dtype=float64)
        if boid.turning:
            direction = boid.cube.centre - boid.location
            change = direction * SP.CONSTRAINT_MULTIPLIER
        boid.adjustment = boid.adjustment + change


class Boid(object):
    """
    A single swarm agent
    """

    def __init__(self, cube, attractors, id):
        """
        Make a baby boid
        :param cube: Cube   bounding box for this boid
        :param attractors: [Attractor]
        """
        self.cube = cube
        self.attractors = attractors
        self.id = id

        # doesn't matter that much where you start
        self.location = rand_point_in_cube(cube, DIMS)

        self.velocity = random_vector(DIMS, -1.0, 1.0)  # vx vy vz
        self.adjustment = zeros(DIMS, dtype=float64)  # to accumulate corrections from rules
        self.turning = False
        self.feeding = False

    def __repr__(self):
        return "Boid - pos:{0}, vel:{1}".format(self.location, self.velocity)

    def __lt__(self, other):
        return (self.location < other.location).all()

    def calc_v(self, all_boids, dist_mat):
        """
        Calculate velocity for next tick by applying the swarming rules
        :param all_boids: List of all boids in the swarm
        :param dist_mat: most likely incomplete distance matrix between boids
        """
        # Apply the rules to each of the boids
        # flocks use alignment, swarms do not
        flock = SP.IS_FLOCK
        rules = [Separation(), Cohesion()]
        if flock:
            rules.append(Alignment())
        # bonus rules don't need the accumulate stage
        bonus_rules = [Constraint(), Attraction()]

        # turns out this is the bottleneck of the whole program...
        for boid in all_boids:
            key = (min(self.id, boid.id), max(self.id, boid.id))
            try:
                distance = dist_mat[key]
            except KeyError:
                distance = norm(self.location-boid.location)
                dist_mat[key] = distance
            for rule in rules:
                if distance < rule.neighbourhood*self.cube.edge_length:
                    rule.accumulate(self, boid, distance)
        self.adjustment = zeros(DIMS, dtype=float64)  # reset adjustment vector
        for rule in rules:  # save corrections to the adjustment
            rule.add_adjustment(self)
        for rule in bonus_rules:
            rule.add_adjustment(self)

    def limit_speed(self, max_speed):
        """
        Ensure the speed does not exceed max_speed
        :param max_speed: float
        """
        # TODO experiment with turning this off. Other than the boids leaving the cube sometimes, it's fine.
        if norm(self.velocity) > max_speed:
            self.velocity = normalise(self.velocity) * max_speed

    def get_location(self):
        """
        :return: position relative to cube (with v_min as origin)
        """
        return self.location - self.cube.v_min

    def get_loc_ratios(self):
        """
        :return: a list of 0-1 proportions of how far the boid is along each axis
        """
        loc = self.get_location()
        # this looks weird but it's just a faster way of iterating over the loc array and clamping values
        for dim in nditer(loc, op_flags=['readwrite']):
            dim[...] = min(0.99, max(0.0, dim/self.cube.edge_length))

        # append velocity to the end (as a fraction of max_speed)
        vel_frac = self.velocity / SP.MAX_SPEED
        append(loc, vel_frac)

        return loc

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
    Attracts boid towards it (by the Attraction rule)
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
        a, b, c, d, e = random.randint(1, 8), random.randint(1, 7), random.randint(1, 5), \
            random.randint(1, 4), random.randint(1, 6)
        # TODO make smaller paths (that loop faster and lead to repetition if followed)
        self.x_f = lambda t: cos(a * pi * t)
        self.y_f = lambda t: sin(b * pi * t)
        self.z_f = lambda t: sin(c * pi * t)
        self.i_f = lambda t: sin(d * pi * t)
        self.j_f = lambda t: cos(e * pi * t)

    def set_pos(self, new_l):
        self.location = new_l

    def step_path_equation(self):
        # TODO set path in n dimensions
        # parametric equations:
        x = self.x_f(self.t)
        y = self.y_f(self.t)
        z = self.z_f(self.t)
        i = self.i_f(self.t)
        j = self.j_f(self.t)
        self.t += self.step
        new_point = array([x, y, z, i, j], dtype=float64)*0.4*self.cube.edge_length + self.cube.centre
        self.set_pos(new_point)


class CentOfMass(object):
    """
    The centre of mass of a swarm
    """
    def __init__(self, location, velocity, v_min, edge_length):
        """
        Set up an initial (probably wrong) centre of mass object
        :param location: array
        :param velocity: array
        :param v_min:    min vertex of bounding box
        :param edge_length: length of each dimension
        """
        self.location = location
        self.velocity = velocity
        self.v_min = v_min
        self.edge_length = edge_length

    def __repr__(self):
        return "Centre of Mass - pos:{0}, vel:{1}".format(self.location, self.velocity)

    def set(self, location, velocity):
        """
        Set the location and velocity of the c.o.m
        :param location: array
        :param velocity: array
        """
        self.location = location
        self.velocity = velocity

    def get_location(self):
        """
        USE THIS RATHER THAN ACCESSING location
        :return: Location relative to v_min (i.e v_min is origin)
        """
        return self.location - self.v_min

    def get_loc_ratios(self):
        """
        :return: a list of 0-1 proportions of how far the COM is along each axis
        """
        loc = self.get_location()
        for dim in nditer(loc, op_flags=['readwrite']):
            dim[...] = min(0.99, max(0.0, dim/self.edge_length))

        # append velocity to the end (as a fraction of max_speed)
        vel_frac = self.velocity / SP.MAX_SPEED
        append(loc, vel_frac)

        return loc


class Swarm(object):
    """
    A swarm of boids
    """
    def __init__(self, num_boids, cube, num_attractors=None, follow=None):
        """
        Set up a swarm
        :param num_boids: int   number of boids in the swarm
        :param cube:      Cube  bounding box of swarm (and its boids)
        """
        super().__init__()
        self.dims = DIMS  # used by interpreter
        self.num_boids = num_boids
        self.num_attractors = num_attractors
        self.boids = []
        self.cube = cube
        self.attractors = []
        self.att_index = 0  # for midi-input mode

        # which attractor update to use
        if SP.ATTRACTOR_MODE == 0:
            self.update_attractors = self.ua_random
        elif SP.ATTRACTOR_MODE == 1:
            self.update_attractors = self.ua_path
        elif SP.ATTRACTOR_MODE == 2:
            self.update_attractors = self.ua_midi
        else:
            print("Unimplemented ATTRACTOR_MODE value: {0}".format(SP.ATTRACTOR_MODE))
            self.update_attractors = self.ua_random

        # TODO STIGMERGY:
        if num_attractors is None:
            # then they are a follower swarm
            # they don't need the update_attractors method
            self.update_attractors = lambda: None
            if follow is None:
                print("ERROR: please state number of attractors for follower swarm")
            else:
                self.num_attractors = follow

        for _ in range(self.num_attractors):
            self.attractors.append(Attractor(rand_point_in_cube(self.cube, DIMS), cube))

        for i in range(num_boids):
            self.boids.append(Boid(cube, self.attractors, i))
        self.c_o_m = CentOfMass(cube.centre, zeros(DIMS, dtype=float64), cube.v_min, cube.edge_length)

    def __repr__(self):
        return "Swarm of {0} boids in cube with min vertex {1}".format(self.num_boids, self.cube.v_min)

    def place_attractor(self, ratios):
        """
        Place an attractor given "ratios"
        :param ratios: ratio of how far along to place attractor on each axis
        """
        # TODO an interpolated path would be better
        v_min = self.cube.v_min
        edge = self.cube.edge_length
        pos = []
        for i, dim in enumerate(ratios):
            pos.append(v_min[i] + dim*edge)
        # update the attractor that has been still longest with this new position
        if self.attractors:
            self.attractors[self.att_index].location = array(pos, dtype=float64)
            self.att_index = (self.att_index + 1) % self.num_attractors  # TODO div0 risk
        return

    def update(self):
        """
        Update every boid in the swarm and calculate the swarm's centre of mass
        """
        # position and velocity accumulators
        p_acc = zeros(DIMS, dtype=float64)
        v_acc = zeros(DIMS, dtype=float64)
        atts = self.attractors
        dist_mat = {}
        for boid in self.boids:
            boid.calc_v(self.boids, dist_mat)
            boid.attractors = atts
        # for boid in self.boids:  # TODO is this line necessary? (calc all v first or one at a time?)
            boid.update()
            p_acc = p_acc + boid.location
            v_acc = v_acc + boid.velocity
        # calculate the centre of mass
        self.c_o_m.set(p_acc / self.num_boids, v_acc / self.num_boids)

        self.update_attractors()

    def ua_random(self):
        """ a chance to update each attractor to a random place """
        for i, attr in enumerate(self.attractors):
            if random.random() < SP.RAND_ATTRACTOR_CHANGE:
                att = Attractor(rand_point_in_cube(self.cube, DIMS), self.cube)
                self.attractors[i] = att

    def ua_path(self):
        """ step through equation function for each attractor """
        for attr in self.attractors:
            attr.step_path_equation()

    def ua_midi(self):
        """ "this is handled by the callback function place_attractor """
        pass

    def get_COM(self):
        """
        :return: the centre of mass of the swarm
        """
        # TODO make this foolproof
        com = self.c_o_m
        return com
