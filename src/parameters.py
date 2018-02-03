"""
User-tweakable parameters
Changed in config.ini
Except for IP, which is changed in JSON files for individual interpreters
"""


class DP:
    """
    Default Params
    i.e. boring things
    """
    UPDATE_RATE = 60                    # screen update, hz


class SP:
    """
    Swarm parameters
    """
    TRUE_RANDOM = -1                    # sets standard for below (not changeable from config.ini)
    RANDOM_SEED = TRUE_RANDOM           # seed for random throughout program TODO doesn't seem to affect Swarm...
    IS_FLOCK = False                    # flock or swarm
    FEEDING = False                     # only play notes when the boids are near food
    FEED_DIST = 10.0                    # distance from which boids can feed on an attractor
    MAX_SPEED = 0.7                     # recommended max of 1.0
    RAND_POINT_SD = 7.5                 # 7.5
    COHESION_NEIGHBOURHOOD = 0.5        # NEIGHBOURHOOD is ratio of edgelength (so 0.5 is from half the cube away)
    ALIGNMENT_NEIGHBOURHOOD = 0.5
    SEPARATION_NEIGHBOURHOOD = 0.1
    COHESION_MULTIPLIER = 0.0006        # 0.0006
    ALIGNMENT_MULTIPLIER = 0.03         # 0.03
    SEPARATION_MULTIPLIER = 0.09        # 0.05 - seems to be a sweet spot (TODO find out why)
    ATTRACTION_MULTIPLIER = 0.005       # 0.005 - larger means more clumping
    CONSTRAINT_MULTIPLIER = 0.001       # 0.001
    TURNING_RATIO = 0.80                # 0.80 - turning if boid is <this>*radius of bounding 'sphere' away from centre
    ATTRACTOR_MODE = 0                  # 0 = teleportation, 1 = paths
    RAND_ATTRACTOR_CHANGE = 0.035       # 0.05
    ATTRACTORS_NOTICED = 2              # How many attractors to be attracted to at once
    MOTION_CONSTANT = 0.035             # Add a bit of speed to keep them going (optional)
    BOUNDING_SPHERE = 1                 # 0 = BOX, 1 = SPHERE to keep the boids inside


class IP:
    """
    Interpreter parameters
    """
    PITCH_MIN = 21      # 21   - A0
    PITCH_RANGE = 88    # 88   - 88 keys on a piano, so seems suitable
    TIME_MIN = 0.05     # 0.05 - min time between events
    TIME_RANGE = 0.25   # 1    - range in time between events
    DYNAM_MIN = 25      # 0    - min dynamic
    DYNAM_RANGE = 102
    PAN_MIN = 30
    PAN_RANGE = 67
    PROBABILITY = 0.75  # 0.75 - prob of playing a note
