"""
User-tweakable parameters
Changed in config.ini
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
    RANDOM_SEED = 72                    # -1 for 'true random'
    TRUE_RANDOM = -1                    # sets standard for above (not changeable from config.ini)
    IS_FLOCK = False                    # flock or swarm
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
    PITCH_RANGE = 88    # 88   - 88 keys on a piano, so seems suitable
    PITCH_MIN = 21      # 21   - A0
    TIME_RANGE = 0.25   # 1    - range in time between events
    TIME_MIN = 0.05     # 0.05 - min time between events
    DYNAM_MAX = 127     # 127  - max dynamic
    DYNAM_MIN = 25      # 0    - min dynamic
    DYNAM_RANGE = DYNAM_MAX - DYNAM_MIN
    CHANNEL_VOL = 110
