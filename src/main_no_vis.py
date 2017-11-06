import Swarm
import PYGAMESwarmRender
import rtmidi
from numpy import r_
from interps import (ChordSequencer, NaiveSequencer)


def main():

    # DEFINE BOUNDING BOX(ES)
    cube_min = r_[10, -5, 7]  # cube min vertex
    edge_length = 50.0
    cube = Swarm.Cube(cube_min, edge_length)

    # MAKE SWARM OBJECTS
    # swarm, channel (starting from 1), instrument code
    swarm_data = [
                    (Swarm.Swarm(7, cube), 1, 56),
                    (Swarm.Swarm(7, cube), 2, 1),
                    (Swarm.Swarm(7, cube), 3, 26),
                    (Swarm.Swarm(7, cube), 9, 0)
                ]
    swarms = list(map(lambda x: x[0], swarm_data))
    renderer = PYGAMESwarmRender.Renderer(False, swarms)

    # SET UP MIDI
    midiout = rtmidi.MidiOut().open_port(0)
    seqs = [NaiveSequencer('1', midiout, swarm_data[0]),
            NaiveSequencer('2', midiout, swarm_data[1]),
            ChordSequencer('3', midiout, swarm_data[2]),
            ChordSequencer('4', midiout, swarm_data[3])]

    print("Press Control-C to quit.")

    try:
        while True:
            renderer.update()
            # sleep(0.001)
    except KeyboardInterrupt:
        print('')
    finally:
        for seq in seqs:
            seq.done = True  # And kill it.
            seq.join()
        del midiout
        print("Done")


if __name__ == "__main__":
    main()
