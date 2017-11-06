import Swarm
from SwarmRender import (Window)
import pyglet
import rtmidi
from Interpreter import (NaiveSequencer, ChordSequencer)

import configparser
import parameters
import random
import sys

from numpy import r_

"""
Main method for running the swarm simulation

"""


def load_config():
    config = configparser.ConfigParser()
    # TODO error catching
    config.read('config.ini')

    parameters.DP.UPDATE_RATE = int(config['DEFAULT']['UPDATE_RATE'])

    parameters.IP.PITCH_RANGE = int(config['INTERPRETER']['PITCH_RANGE'])
    parameters.IP.PITCH_MIN = int(config['INTERPRETER']['PITCH_MIN'])
    parameters.IP.TIME_RANGE = float(config['INTERPRETER']['TIME_RANGE'])
    parameters.IP.TIME_MIN = float(config['INTERPRETER']['TIME_MIN'])
    parameters.IP.DYNAM_MAX = int(config['INTERPRETER']['DYNAM_MAX'])
    parameters.IP.DYNAM_MIN = int(config['INTERPRETER']['DYNAM_MIN'])
    parameters.IP.CHANNEL_VOL = int(config['INTERPRETER']['CHANNEL_VOL'])

    rs = int(config['SWARM']['RANDOM_SEED'])
    if rs != -1:
        parameters.SP.RANDOM_SEED = rs
    else:
        seed = random.randrange(sys.maxsize)  # TODO always gives me 5249979066121302517...
        print("Using seed " + str(seed))
        parameters.SP.RANDOM_SEED = seed
    parameters.SP.IS_FLOCK = int(config['SWARM']['IS_FLOCK'])  # TODO bool
    parameters.SP.MAX_SPEED = float(config['SWARM']['MAX_SPEED'])
    parameters.SP.RAND_POINT_SD = float(config['SWARM']['RAND_POINT_SD'])
    parameters.SP.COHESION_NEIGHBOURHOOD = float(config['SWARM']['COHESION_NEIGHBOURHOOD'])
    parameters.SP.ALIGNMENT_NEIGHBOURHOOD = float(config['SWARM']['ALIGNMENT_NEIGHBOURHOOD'])
    parameters.SP.SEPARATION_NEIGHBOURHOOD = float(config['SWARM']['SEPARATION_NEIGHBOURHOOD'])
    parameters.SP.COHESION_MULTIPLIER = float(config['SWARM']['COHESION_MULTIPLIER'])
    parameters.SP.ALIGNMENT_MULTIPLIER = float(config['SWARM']['ALIGNMENT_MULTIPLIER'])
    parameters.SP.SEPARATION_MULTIPLIER = float(config['SWARM']['SEPARATION_MULTIPLIER'])
    parameters.SP.ATTRACTION_MULTIPLIER = float(config['SWARM']['ATTRACTION_MULTIPLIER'])
    parameters.SP.CONSTRAINT_MULTIPLIER = float(config['SWARM']['CONSTRAINT_MULTIPLIER'])
    parameters.SP.TURNING_RATIO = float(config['SWARM']['TURNING_RATIO'])
    parameters.SP.RAND_ATTRACTOR_CHANGE = float(config['SWARM']['RAND_ATTRACTOR_CHANGE'])


def main():

    # LOAD PARAMS FROM CONFIG
    load_config()

    # DEFINE BOUNDING BOX(ES)
    cube_min = r_[-10, -5, -7]  # cube min vertex
    edge_length = 20.0

    cube = Swarm.Cube(cube_min, edge_length)

    cube2 = Swarm.Cube(r_[40, -10, 17], 30)

    # MAKE SWARM OBJECTS
    # swarm, channel (starting from 1), instrument code
    swarm_data = [
                    # (Swarm.Swarm(7, cube), 1, 56),
                    (Swarm.Swarm(7, cube), 2, 88),
                    (Swarm.Swarm(7, cube2), 3, 26),
                    # (Swarm.Swarm(7, cube2), 9, 0)
    ]
    swarms = list(map(lambda x: x[0], swarm_data))

    # SET UP MIDI
    midiout = rtmidi.MidiOut().open_port(0)
    seqs = [NaiveSequencer(str(i + 1), midiout, swarm_data[i]) for i in range(len(swarm_data))]

    config = pyglet.gl.Config(sample_buffers=1, samples=4)

    # creates the window and sets its properties
    window = Window(swarms, config=config, width=1200, height=900, caption='Swarm Music', resizable=True)

    # starts the application
    pyglet.app.run()

    # CLEAN UP
    for seq in seqs:
        seq.done = True  # And kill it.
        seq.join()
    del midiout
    print("Exiting")

if __name__ == '__main__':
    main()
