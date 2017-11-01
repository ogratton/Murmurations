from datetime import datetime  # temp

import Swarm
from SwarmRender import (Window)
import pyglet
import rtmidi
from Interpreter import Sequencer
from rtmidi.midiconstants import (ALL_SOUND_OFF, CHANNEL_VOLUME,
                                  CONTROL_CHANGE, NOTE_ON, NOTE_OFF, PROGRAM_CHANGE)

from vectors import Vector3

# TODO IN THE MIDDLE OF TRANSITIONING TO PYGLET SO THIS IS ALL SHIT

"""
Main method for running the swarm simulation

"""


def main():

    # DEFINE BOUNDING BOX(ES)
    cube_min = Vector3([10, 5, 7])  # cube min vertex
    edge_length = 20.0

    cube = Swarm.Cube(cube_min, edge_length)

    cube2 = Swarm.Cube(Vector3([40, -10, 17]), 30)

    # MAKE SWARM OBJECTS
    # swarm, channel (starting from 1), instrument code
    swarm_data = [
                    (Swarm.Swarm(20, cube), 1, 56),
                    (Swarm.Swarm(7, cube), 2, 1),
                    (Swarm.Swarm(7, cube2), 3, 26),
                    (Swarm.Swarm(7, cube2), 9, 0)
    ]
    swarms = list(map(lambda x: x[0], swarm_data))

    # SET UP MIDI
    midiout = rtmidi.MidiOut().open_port(0)
    seqs = [Sequencer(str(i+1), midiout, swarm_data[i]) for i in range(len(swarm_data))]

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
