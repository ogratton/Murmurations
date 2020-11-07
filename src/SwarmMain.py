import Swarm
from SwarmRender import Window
import pyglet
import rtmidi
from Interpreters import *

import random
import Scales
import configparser
import Parameters
from InStream import InStream

from numpy import array

"""
Main method for running the swarm simulation

"""


def load_config():
    config = configparser.ConfigParser()
    # TODO error catching
    config.read("config.ini")

    Parameters.DP.UPDATE_RATE = int(config["DEFAULT"]["UPDATE_RATE"])

    seed = int(config["SWARM"]["RANDOM_SEED"])
    if seed == -1:
        seed = random.randint(1, 1000000)
    Parameters.SP.RANDOM_SEED = seed
    Parameters.SP.IS_FLOCK = int(config["SWARM"]["IS_FLOCK"])
    Parameters.SP.FEEDING = int(config["SWARM"]["FEEDING"])
    Parameters.SP.FEED_DIST = float(config["SWARM"]["FEED_DIST"])
    Parameters.SP.MAX_SPEED = float(config["SWARM"]["MAX_SPEED"])
    Parameters.SP.RAND_POINT_SD = float(config["SWARM"]["RAND_POINT_SD"])
    Parameters.SP.REPULSION_POINT = float(config["SWARM"]["REPULSION_POINT"])
    Parameters.SP.COHESION_NEIGHBOURHOOD = float(
        config["SWARM"]["COHESION_NEIGHBOURHOOD"]
    )
    Parameters.SP.ALIGNMENT_NEIGHBOURHOOD = float(
        config["SWARM"]["ALIGNMENT_NEIGHBOURHOOD"]
    )
    Parameters.SP.SEPARATION_NEIGHBOURHOOD = float(
        config["SWARM"]["SEPARATION_NEIGHBOURHOOD"]
    )
    Parameters.SP.COHESION_MULTIPLIER = float(config["SWARM"]["COHESION_MULTIPLIER"])
    Parameters.SP.ALIGNMENT_MULTIPLIER = float(config["SWARM"]["ALIGNMENT_MULTIPLIER"])
    Parameters.SP.SEPARATION_MULTIPLIER = float(
        config["SWARM"]["SEPARATION_MULTIPLIER"]
    )
    Parameters.SP.ATTRACTION_MULTIPLIER = float(
        config["SWARM"]["ATTRACTION_MULTIPLIER"]
    )
    Parameters.SP.CONSTRAINT_MULTIPLIER = float(
        config["SWARM"]["CONSTRAINT_MULTIPLIER"]
    )
    Parameters.SP.TURNING_RATIO = float(config["SWARM"]["TURNING_RATIO"])
    Parameters.SP.RAND_ATTRACTOR_CHANGE = float(
        config["SWARM"]["RAND_ATTRACTOR_CHANGE"]
    )
    Parameters.SP.ATTRACTOR_MODE = int(config["SWARM"]["ATTRACTOR_MODE"])
    Parameters.SP.ATTRACTORS_NOTICED = int(config["SWARM"]["ATTRACTORS_NOTICED"])
    Parameters.SP.MOTION_CONSTANT = float(config["SWARM"]["MOTION_CONSTANT"])
    Parameters.SP.BOUNDING_SPHERE = int(config["SWARM"]["BOUNDING_SPHERE"])


def start_interp(interp, tempo=None, scale=None, preset=None, instrument=None):
    if preset:
        preset_path = "./presets/{}.json".format(preset)
        interp.setup_interp(preset_path)
    if tempo:
        interp.set_tempo(tempo)
    if scale:
        interp.set_scale(scale)
    if instrument:
        interp.set_instrument(instrument)
    interp.start()
    return interp


def main(out_port, in_port):

    # LOAD PARAMS FROM CONFIG
    load_config()

    # DEFINE BOUNDING BOX(ES)
    cube_min = array([10, 50, 7, 0, 0])
    edge_length = 40  # 35
    cube = Swarm.Cube(cube_min, edge_length)
    cube2 = Swarm.Cube(array([10 + edge_length, 50, 7, 0, 0]), edge_length)
    cube3 = Swarm.Cube(array([10 + 2 * edge_length, 50, 7, 0, 0]), edge_length)

    # MAKE SWARM OBJECTS
    # TODO make the 'follow' implicit
    # format:       swarm,                    channel
    swarm_data = [
        (Swarm.Swarm(13, cube, 6), 3),
        # (Swarm.Swarm(7, cube, follow=7), 1),
        # (Swarm.Swarm(15, cube3, follow=12), 2),
        # (Swarm.Swarm(4, cube2, follow=7), 9)
    ]
    swarms = list(map(lambda x: x[0], swarm_data))

    # SET UP MIDI
    midiout = rtmidi.MidiOut()
    midiout.open_port(out_port)

    interps = list()
    i1 = PolyInterpreter(0, midiout, swarm_data[0])
    start_interp(i1, tempo=120, scale=Scales.satie, preset="piano", instrument="")
    interps.append(i1)

    # i2 = PolyInterpreter(1, midiout, swarm_data[1])
    # start_interp(i2, tempo=130, scale=Scales.chrom, preset="piano", instrument="")
    # interps.append(i2)
    # #
    # i3 = PolyInterpreter(2, midiout, swarm_data[2])
    # start_interp(i3, tempo=90, scale=Scales.satie, preset="synth", instrument="fantasia")
    # interps.append(i3)

    # start up the midi in stream
    # in_stream = None
    if Parameters.SP.ATTRACTOR_MODE == 2:
        in_stream = InStream(interps, in_port)
        ren_att = True
    else:
        in_stream = None
        ren_att = False

    config = pyglet.gl.Config(sample_buffers=1, samples=4)

    # resolution
    import os

    if os.name != "nt":
        w = 1200
        h = 900
    else:
        w = 1920
        h = 1080

    # creates the window and sets its properties
    Window(
        swarms,
        interps,
        ren_att,
        config=config,
        width=w,
        height=h,
        caption="Murmurations",
        resizable=True,
    )

    # start the application
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


if __name__ == "__main__":

    # on linux I use port 1, windows I use port 1
    # change to whichever port you need
    out_port = 0
    in_port = 0

    import os

    if os.name != "nt":
        in_port = 0
        out_port = 1

    main(out_port, in_port)
