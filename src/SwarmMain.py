import Swarm
from SwarmRender import Window
import pyglet
import rtmidi
from Interpreter import *

import scales
import configparser
import parameters
import instruments as inst

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

    parameters.SP.RANDOM_SEED = int(config['SWARM']['RANDOM_SEED'])
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
    parameters.SP.ATTRACTOR_MODE = int(config['SWARM']['ATTRACTOR_MODE'])
    parameters.SP.ATTRACTORS_NOTICED = int(config['SWARM']['ATTRACTORS_NOTICED'])
    parameters.SP.MOTION_CONSTANT = float(config['SWARM']['MOTION_CONSTANT'])

def main():

    # LOAD PARAMS FROM CONFIG
    load_config()

    # DEFINE BOUNDING BOX(ES)
    cube_min = r_[10, 50, 7]
    edge_length = 50
    cube = Swarm.Cube(cube_min, edge_length)
    cube2 = Swarm.Cube(r_[40, 10, 17], 30)

    # MAKE SWARM OBJECTS
    # swarm, channel (starting from 1), instrument code
    swarm_data = [
                    (Swarm.Swarm(7, cube), 1, inst.PAD_2_WARM),
                    # (Swarm.Swarm(7, cube, 3), 2, inst.KALIMBA),
                    # (Swarm.Swarm(7, cube2), 3, inst.CLAVINET),
                    # (Swarm.Swarm(7, cube2), 9, 0)
    ]
    swarms = list(map(lambda x: x[0], swarm_data))

    # SET UP MIDI
    # TODO TEMP AUDIO OFF
    # midiout = rtmidi.MidiOut().open_port(0)
    # seqs = [ChordSequencer(str(i + 1), midiout, swarm_data[i]) for i in range(len(swarm_data))]

    # seqs[0].set_tempo(120)
    # seqs[1].set_tempo(60)
    # seqs[0].set_scale(scales.min_pen)
    # seqs[1].set_scale(scales.min_arp)
    # map(lambda x: x.set_tempo(120), seqs)
    # map(lambda x: x.set_scale(scales.min_arp), seqs)

    config = pyglet.gl.Config(sample_buffers=1, samples=4)

    # creates the window and sets its properties
    window = Window(swarms, config=config, width=1200, height=900, caption='Swarm Music', resizable=True)

    # starts the application
    pyglet.app.run()

    # CLEAN UP
    # for seq in seqs:
    #     seq.done = True  # And kill it.
    #     seq.join()
    # del midiout
    print("Exiting")

if __name__ == '__main__':
    main()
