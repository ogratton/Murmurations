# cython: profile=True

# Adapted from code by Tom Marble
# https://github.com/tmarble/pyboids/blob/master/boids.py

import random
import numpy as np
cimport numpy as np
cimport cython
from numpy import array, zeros
from numpy.linalg import norm
from parameters import SP
from heapq import (heappush, heappop)  # TODO inefficient
from libc.math cimport sin, cos, M_PI as pi

DTYPE = np.float64
ctypedef np.float64_t DTYPE_t

cdef inline int int_max(int a, int b): return a if a >= b else b
cdef inline int int_min(int a, int b): return a if a <= b else b

cdef inline float float_max(float a, float b): return a if a >= b else b
cdef inline float float_min(float a, float b): return a if a <= b else b

# TODO TEMP
random.seed(SP.RANDOM_SEED)


cpdef float random_range(float lower=0.0, float upper=1.0):
    """
    :return: a random number between lower and upper
    """
    cdef float result = lower + (random.random() * (upper - lower))
    return result


cpdef np.ndarray[DTYPE_t, ndim=1] random_vector(int dims, float lower=0.0, float upper=1.0):
    """
    :param dims: number of dimensions of resultant vector
    :param lower: float lower bound for random_range
    :param upper: float upper bound for random_range
    :return: a vector with <dims> random elements between lower and upper
    """
    cdef np.ndarray[DTYPE_t, ndim=1] result = array([random_range(lower, upper) for _ in range(dims)], dtype=DTYPE)
    return result


cpdef np.ndarray[DTYPE_t, ndim=1] rand_point_in_cube(Cube cube, int dims):
    """
    done with gauss for n dims
    :param cube: Cube object
    :param dims: number of dimensions
    :return:
    """
    cdef float edge = cube.edge_length
    cdef float sd = edge/SP.RAND_POINT_SD

    cdef np.ndarray[DTYPE_t, ndim=1] points
    points = zeros(3, dtype=DTYPE)

    cdef int i
    cdef float p = 0
    for i in range(dims):
        while True:
            p = random.gauss(edge/2, sd)
            if float_max(0, float_min(p, edge)) not in [0, edge]:
                break
        points[i] = p + cube.v_min[i]

    return points


cpdef np.ndarray[DTYPE_t, ndim=1] normalise(np.ndarray[DTYPE_t, ndim=1] vector):
    """
    Normalise a numpy array vector
    :param vector: array
    :return: array normalised
    """
    cdef np.ndarray[DTYPE_t, ndim=1] result = vector/norm(vector)
    return result


cdef class Cube(object):
    """
    Bounding box for swarm
    """
    cdef:
        public np.ndarray v_min
        public float edge_length
        public np.ndarray centre

    def __init__(Cube self, np.ndarray[DTYPE_t, ndim=1] v_min, float edge_length):
        """
        Set up a bounding box that constrains the swarm(s)
        :param v_min:       array      the minimum vertex of the cube (closest to origin)
        :param edge_length: float   the length of each edge (currently always a perfect cube)
        """

        self.v_min = v_min
        self.edge_length = edge_length
        pos = [j + 0.5 * edge_length for j in v_min]
        self.centre = array(pos, dtype=DTYPE)

    def __repr__(Cube self):
        return "Cube from {0} with edge length {1}".format(self.v_min, self.edge_length)


cdef class Rule(object):
    """
    Template for rules of flocking
    """

    cdef:
        np.ndarray change
        int num
        public float neighbourhood

    def __init__(Rule self):
        """
        Initialise aggregators change and num
        Set potency of rule ('neighbourhood')
        """
        self.change = zeros(3, dtype=DTYPE)   # velocity correction
        self.num = 0                          # number of participants
        self.neighbourhood = 0.5              # sphere of view of boid as ratio of cube edge length (overwritten later)

    cpdef void accumulate(Rule self, Boid boid, Boid other, float distance):
        """
        Save any corrections based on other boid to self.change
        """
        pass

    cpdef void add_adjustment(Rule self, Boid boid):
        """
        Add the accumulated self.change to boid.adjustment
        """
        pass


cdef class Cohesion(Rule):
    """ Rule 1: Boids try to fly towards the centre of mass of neighbouring boids. """

    def __init__(Cohesion self):
        super().__init__()
        self.neighbourhood = SP.COHESION_NEIGHBOURHOOD

    cpdef void accumulate(Cohesion self, Boid boid, Boid other, float distance):
        if other != boid:
            self.change += other.location
            self.num += 1

    cpdef void add_adjustment(Cohesion self, Boid boid):
        cdef np.ndarray[DTYPE_t, ndim=1] centroid, desired
        if self.num > 0:
            centroid = self.change / self.num
            desired = centroid - boid.location
            self.change = (desired - boid.velocity) * SP.COHESION_MULTIPLIER
        boid.adjustment += self.change


cdef class Alignment(Rule):
    """ Rule 2: Boids try to match velocity with near boids. """

    def __init__(Alignment self):
        super().__init__()
        self.neighbourhood = SP.ALIGNMENT_NEIGHBOURHOOD

    cpdef void accumulate(Alignment self, Boid boid, Boid other, float distance):
        if other != boid:
            self.change += other.velocity
            self.num += 1

    cpdef void add_adjustment(Alignment self, Boid boid):
        if self.num > 0:
            group_velocity = self.change / self.num
            self.change = (group_velocity - boid.velocity) * SP.ALIGNMENT_MULTIPLIER
        boid.adjustment += self.change


cdef class Separation(Rule):
    """ Rule 3: Boids try to keep a small distance away from other objects (including other boids). """

    def __init__(Separation self):
        super().__init__()
        self.neighbourhood = SP.SEPARATION_NEIGHBOURHOOD

    cpdef void accumulate(Separation self, Boid boid, Boid other, float distance):
        # calc vector from boid2 to boid1 (NOT other way round as we want repulsion)
        repulsion = boid.location - other.location
        if distance > 0:
            # this normalises the repulsion vector and makes closer boids repel more
            self.change += repulsion / distance**2  # makes it an inverse square rule
        self.num += 1

    cpdef void add_adjustment(Separation self, Boid boid):
        # here norm is vector magnitude
        if norm(self.change) > 0:
            group_separation = self.change / self.num
            self.change = (group_separation - boid.velocity) * SP.SEPARATION_MULTIPLIER
        boid.adjustment += self.change


cdef class Attraction:
    """ Bonus Rule: Fly towards the attractor(s) """

    # TODO optimise

    @staticmethod
    def add_adjustment(Boid boid):
        # priority queue of (distance, change)
        dist_mat = []

        cdef Attractor attr
        for attr in boid.attractors:
            to_attractor = attr.location - boid.location
            dist = norm(to_attractor)
            # 1/dist makes attraction stronger for closer attractors
            change = (to_attractor - boid.velocity) * SP.ATTRACTION_MULTIPLIER * (1/dist)
            heappush(dist_mat, (dist, list(change)))  # needs to be a list as nparray is 'ambiguous'

        # only feel the pull of the nearest <x> attractors
        attention_span = min(SP.ATTRACTORS_NOTICED, len(boid.attractors))
        for _ in range(attention_span):
            boid.adjustment += heappop(dist_mat)[1]


cdef class Constraint:
    """ Bonus Rule: Boids must stay within the bounding cube. """

    @staticmethod
    def add_adjustment(Boid boid):
        change = zeros(3, dtype=DTYPE)
        if boid.turning:
            direction = boid.cube.centre - boid.location
            change = direction * SP.CONSTRAINT_MULTIPLIER
        boid.adjustment = boid.adjustment + change


@cython.freelist(50) # typical max number
cdef class Boid(object):
    """
    A single swarm agent
    """

    cdef:
        public Cube cube
        public np.ndarray attractors
        public int id
        public np.ndarray location
        public np.ndarray velocity
        public np.ndarray adjustment
        public int turning

    def __init__(Boid self, Cube cube, attractors, int id):
        """
        Make a baby boid
        :param cube: Cube   bounding box for this boid
        :param attractors: [Attractor]
        """
        self.cube = cube
        self.attractors = attractors
        self.id = id

        # doesn't matter that much where you start
        self.location = rand_point_in_cube(cube, 3)

        self.velocity = random_vector(3, -1.0, 1.0)  # vx vy vz
        self.adjustment = zeros(3, dtype=DTYPE)  # to accumulate corrections from rules
        self.turning = 0

    def __repr__(Boid self):
        return "Boid - pos:{0}, vel:{1}".format(self.location, self.velocity)

    cpdef void calc_v(Boid self, np.ndarray[object, ndim=1] all_boids, dist_mat):
        """
        Calculate velocity for next tick by applying the swarming rules
        :param all_boids: List of all boids in the swarm
        :param dist_mat: most likely incomplete distance matrix between boids
        """
        # Apply the rules to each of the boids
        # flocks use alignment, swarms do not
        cdef int flock = SP.IS_FLOCK
        rules = [Separation(), Cohesion()]
        if flock:
            rules.append(Alignment())
        # bonus rules don't need the accumulate stage
        bonus_rules = [Constraint(), Attraction()]

        # TODO this makes the swarm closer to O(n^2) than linear. Maybe find a better data structure than list
        # turns out this is the bottleneck of the whole program...
        cdef Boid boid
        cdef float distance
        for boid in all_boids:
            # TODO test if it's faster with dist_mat
            key = (int_min(self.id, boid.id), int_max(self.id, boid.id))
            try:
                distance = dist_mat[key]
            except KeyError:
                distance = norm(self.location-boid.location)
                dist_mat[key] = distance
            #distance = norm(self.location-boid.location)
            for rule in rules:
                if distance < rule.neighbourhood*self.cube.edge_length:
                    rule.accumulate(self, boid, distance)
        self.adjustment = zeros(3, dtype=DTYPE)  # reset adjustment vector
        for rule in rules:  # save corrections to the adjustment
            rule.add_adjustment(self)
        for rule in bonus_rules:
            rule.add_adjustment(self)

    def limit_speed(Boid self, float max_speed):
        """
        Ensure the speed does not exceed max_speed
        :param max_speed: float
        """
        if norm(self.velocity) > max_speed:
            self.velocity = normalise(self.velocity) * max_speed

    def get_location(Boid self):
        """
        :return: position relative to cube (with v_min as origin)
        """
        return self.location - self.cube.v_min

    def update(Boid self):
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

        # TODO optimise

        if SP.BOUNDING_SPHERE:
            self.turning = (norm(self.location-self.cube.centre) >= self.cube.edge_length*SP.TURNING_RATIO/2)
        else:
            self.turning = 0
            for dim in range(len(self.location)):
                self.turning = self.turning or norm(self.location[dim]-self.cube.centre[dim]) >= self.cube.edge_length*SP.TURNING_RATIO/2


cdef class Attractor(object):
    """
    Attracts boid towards it (by the Attraction rule)
    """

    cdef:
        public np.ndarray location
        public Cube cube
        float t, step
        int a, b, c

    def __init__(Attractor self, location, cube):
        self.location = location
        # TODO experimental values used here
        self.cube = cube
        self.t = random.random()  # start a random way along
        self.step = random.randrange(50, 200)/100000  # at a random speed too

        # make a random parametric path
        # in this 3d example, the dimension that we leave "pi" out of varies less
        # so if x is dynamic and x_f is simply cos(4t) then it will move slower and have
        # less dynamic interest
        self.a = random.randint(1, 8)
        self.b = random.randint(1, 8)
        self.c = random.randint(1, 8)

    cdef inline float x_f(Attractor self, float t): return cos(self.a*t)

    cdef inline float y_f(Attractor self, float t): return sin(self.b*pi*t)

    cdef inline float z_f(Attractor self, float t): return sin(self.c*pi*t)

    def set_pos(Attractor self, np.ndarray[DTYPE_t, ndim=1] new_l):
        self.location = new_l

    def step_path_equation(Attractor self):
        # TODO set path in n dimensions
        # parametric equations:
        x = self.x_f(self.t)
        y = self.y_f(self.t)
        z = self.z_f(self.t)
        self.t += self.step
        new_point = array([x, y, z], dtype=DTYPE)*0.4*self.cube.edge_length + self.cube.centre
        self.set_pos(new_point)


cdef class CentOfMass(object):
    """
    The centre of mass of a swarm
    """

    cdef:
        public np.ndarray location
        public np.ndarray velocity
        public np.ndarray v_min

    def __init__(self, location, velocity, v_min):
        """
        Set up an initial (probably wrong) centre of mass object
        :param location: array
        :param velocity: array
        :param v_min:    array min vertex of bounding box
        """
        self.location = location
        self.velocity = velocity
        self.v_min = v_min

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


@cython.freelist(4) # supports more but rarely needed
cdef class Swarm(object):
    """
    A swarm of boids
    """

    cdef:
        public int num_boids, num_attractors
        public np.ndarray boids, attractors
        public Cube cube
        int att_index
        public CentOfMass c_o_m

    def __init__(self, num_boids, cube, num_attractors=1):
        """
        Set up a swarm
        :param num_boids: int   number of boids in the swarm
        :param cube:      Cube  bounding box of swarm (and its boids)
        """
        super().__init__()
        self.num_boids = num_boids
        self.num_attractors = num_attractors
        self.boids = array([None]*num_boids, dtype=Boid)
        self.attractors = array([None]*num_attractors, dtype=Attractor)
        self.att_index = 0  # for midi-input mode
        self.cube = cube
        cdef int j
        for j in range(num_attractors):
            self.attractors[j] = Attractor(rand_point_in_cube(self.cube, 3), cube)  # or cube.centre
        cdef int i
        for i in range(num_boids):
            self.boids[i] = Boid(cube, self.attractors, i)
        self.c_o_m = CentOfMass(cube.centre, zeros(3, dtype=DTYPE), cube.v_min)

        # TODO this doesn't actually work here
        if SP.RANDOM_SEED != SP.TRUE_RANDOM:
            random.seed(SP.RANDOM_SEED)  # for repeatability

    def __repr__(self):
        return "Swarm of {0} boids in cube with min vertex {1}".format(self.num_boids, self.cube.v_min)

    def place_attractor(self, ratios):
        """
        Place an attractor given "ratios"
        :param ratios: ratio of how far along to place attractor on each axis
        """
        cube = self.cube
        v_min = cube.v_min
        edge = cube.edge_length
        pos = []
        for i, dim in enumerate(ratios):
            pos.append(v_min[i] + dim*edge)
        # update the attractor that has been still longest with this new position
        self.attractors[self.att_index].location = array(pos, dtype=DTYPE)
        self.att_index = (self.att_index + 1) % self.num_attractors  # TODO div0 risk
        return

    cpdef void update(Swarm self):
        """
        Update every boid in the swarm and calculate the swarm's centre of mass
        """
        # TODO optimise

        # position and velocity accumulators
        cdef:
            np.ndarray[DTYPE_t, ndim=1] p_acc = zeros(3, dtype=DTYPE)
            np.ndarray[DTYPE_t, ndim=1] v_acc = zeros(3, dtype=DTYPE)
            Boid boid
        dist_mat = {}
        for boid in self.boids:
            boid.calc_v(self.boids, dist_mat)
            boid.attractors = self.attractors
        for boid in self.boids:  # TODO is this line necessary? (calc all v first or one at a time?)
            boid.update()
            p_acc = p_acc + boid.location
            v_acc = v_acc + boid.velocity
        # calculate the centre of mass
        cdef int nb = self.num_boids
        p_acc = p_acc / nb
        v_acc = v_acc / nb
        self.c_o_m.set(p_acc, v_acc)

        # update attractors
        if SP.ATTRACTOR_MODE == 0:
            self.randAttractorMode_update()
        elif SP.ATTRACTOR_MODE == 1:
            self.parametricAttractorMode_update()
        elif SP.ATTRACTOR_MODE == 2:
            self.midiAttractorMode_update()
        else:
            print("Unimplemented ATTRACTOR_MODE value: {0}".format(SP.ATTRACTOR_MODE))
            SP.ATTRACTOR_MODE = 0

    cpdef void randAttractorMode_update(Swarm self):
        cdef int i
        cdef Attractor attr
        for i, attr in enumerate(self.attractors):
            if random.random() < SP.RAND_ATTRACTOR_CHANGE:
                att = Attractor(rand_point_in_cube(self.cube, 3), self.cube)
                self.attractors[i] = att

    cpdef void parametricAttractorMode_update(Swarm self):
        cdef Attractor attr
        for attr in self.attractors:
            attr.step_path_equation()

    def midiAttractorMode_update(self):
        """ this is handled by the callback function midi_to_attractor """
        pass


    cpdef CentOfMass get_COM(Swarm self):
        """
        WARNING: MUST USE com.get_location()
        :return: the centre of mass of the swarm
        """
        # TODO make this foolproof
        com = self.c_o_m
        return com
