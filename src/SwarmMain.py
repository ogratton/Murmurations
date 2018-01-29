import Swarm
from SwarmRender import Window
import pyglet
import rtmidi
from Interpreter import *
from Interpreters import *

import random
import Scales
import configparser
import Parameters
import Instruments as inst
from midi_in_stream import InStream, DummyInStream

from numpy import array

"""
Main method for running the swarm simulation

"""


def load_config():
    config = configparser.ConfigParser()
    # TODO error catching
    config.read('config.ini')

    Parameters.DP.UPDATE_RATE = int(config['DEFAULT']['UPDATE_RATE'])

    seed = int(config['SWARM']['RANDOM_SEED'])
    if seed == -1:
        seed = random.randint(1, 1000000)
    Parameters.SP.RANDOM_SEED = seed
    Parameters.SP.IS_FLOCK = int(config['SWARM']['IS_FLOCK'])  # TODO bool
    Parameters.SP.MAX_SPEED = float(config['SWARM']['MAX_SPEED'])
    Parameters.SP.RAND_POINT_SD = float(config['SWARM']['RAND_POINT_SD'])
    Parameters.SP.COHESION_NEIGHBOURHOOD = float(config['SWARM']['COHESION_NEIGHBOURHOOD'])
    Parameters.SP.ALIGNMENT_NEIGHBOURHOOD = float(config['SWARM']['ALIGNMENT_NEIGHBOURHOOD'])
    Parameters.SP.SEPARATION_NEIGHBOURHOOD = float(config['SWARM']['SEPARATION_NEIGHBOURHOOD'])
    Parameters.SP.COHESION_MULTIPLIER = float(config['SWARM']['COHESION_MULTIPLIER'])
    Parameters.SP.ALIGNMENT_MULTIPLIER = float(config['SWARM']['ALIGNMENT_MULTIPLIER'])
    Parameters.SP.SEPARATION_MULTIPLIER = float(config['SWARM']['SEPARATION_MULTIPLIER'])
    Parameters.SP.ATTRACTION_MULTIPLIER = float(config['SWARM']['ATTRACTION_MULTIPLIER'])
    Parameters.SP.CONSTRAINT_MULTIPLIER = float(config['SWARM']['CONSTRAINT_MULTIPLIER'])
    Parameters.SP.TURNING_RATIO = float(config['SWARM']['TURNING_RATIO'])
    Parameters.SP.RAND_ATTRACTOR_CHANGE = float(config['SWARM']['RAND_ATTRACTOR_CHANGE'])
    Parameters.SP.ATTRACTOR_MODE = int(config['SWARM']['ATTRACTOR_MODE'])
    Parameters.SP.ATTRACTORS_NOTICED = int(config['SWARM']['ATTRACTORS_NOTICED'])
    Parameters.SP.MOTION_CONSTANT = float(config['SWARM']['MOTION_CONSTANT'])
    Parameters.SP.BOUNDING_SPHERE = int(config['SWARM']['BOUNDING_SPHERE'])


def main():

    # LOAD PARAMS FROM CONFIG
    load_config()

    # DEFINE BOUNDING BOX(ES)
    cube_min = array([10, 50, 7, 0, 0])
    edge_length = 30
    cube = Swarm.Cube(cube_min, edge_length)
    # cube2 = Swarm.Cube(array([40, 10, 17, 0, 0]), 30)

    # MAKE SWARM OBJECTS
    # swarm, channel, instrument code (bank, pc)
    swarm_data = [
                    (Swarm.Swarm(7, cube, 6), 0, inst.GLOCKENSPIEL),
                    # (Swarm.Swarm(7, cube, 2), 1, inst.PICKED_BASS),
                    # (Swarm.Swarm(7, cube, 6), 2, inst.TRUMPET),
                    # (Swarm.Swarm(3, cube, 6), 9, inst.YAMAHA_GRAND_PIANO)
    ]
    swarms = list(map(lambda x: x[0], swarm_data))

    # SET UP MIDI
    midiout = rtmidi.MidiOut()
    # for port_name in midiout.get_ports():
    #     print(port_name)
    midiout.open_port(0)
    # interps = [ChordSequencer(midiout, swarm_d) for swarm_d in swarm_data]
    # interps = [MonoInterpreter(midiout, swarm_d) for swarm_d in swarm_data]

    interps = list()
    interps.append(RandomNotes(0, midiout, swarm_data[0]))
    interps[0].setup_interp("./presets/_piano.json")
    interps[0].set_tempo(80)
    interps[0].set_scale(Scales.locrian)
    # interps.append(MonoInterpreter(1, midiout, swarm_data[1]))
    # interps[1].setup_interp("./presets/_bass.json")
    # interps[1].set_tempo(80)
    # interps[1].set_scale(Scales.aeolian)
    # interps.append(PolyInterpreter(2, midiout, swarm_data[2]))
    # interps[2].setup_interp("./presets/_piano.json")
    # interps[2].set_tempo(120)
    # interps[2].set_scale(Scales.min_pen)

    # start up the midi in stream
    in_stream = None
    if Parameters.SP.ATTRACTOR_MODE == 2:
        in_stream = InStream(interps, 0)

    config = pyglet.gl.Config(sample_buffers=1, samples=4)

    # creates the window and sets its properties
    # TODO don't really like the idea of passing the swarms and the interpreters
    window = Window(swarms, interps, config=config, width=1200, height=900, caption='Swarm Music', resizable=True)

    # starts the application
    pyglet.app.run()

    # CLEAN UP
    for interp in interps:
        interp.done = True  # kill it.
        interp.join()
    del midiout
    if in_stream:
        in_stream.done = True
        in_stream.join()
    print("Exiting")

if __name__ == '__main__':
    main()
