import Swarm
import SwarmMain
import rtmidi
from numpy import r_
from Interpreter import *
import scales
import instruments as inst
from time import sleep

"""
launch the program without the display
"""


class Manager:
    """
    Contains the swarm object(s) and cubes
    """

    def __init__(self, swarms):
        """
        :param swarms: set{Swarm}   set of swarms
        """
        super().__init__()
        self.swarms = swarms
        self.cubes = set()
        for swarm in swarms:
            self.cubes.add(swarm.cube)

    def __repr__(self):
        return "TODO - Managerr"

    def add_swarm(self, swarm):
        """
        Allows a swarm to be added in real-time without restarting
        :param swarm: Swarm     new swarm
        """
        self.swarms.append(swarm)
        self.cubes.add(swarm.cube)

    def update(self):
        """
        Update all the swarms
        """
        for swarm in self.swarms:
            swarm.update()


class Runner(threading.Thread):

    def __init__(self, manager):
        super(Runner, self).__init__()
        self.manager = manager
        self.done = False

    def run(self):
        while not self.done:
            self.manager.update()


def main():

    SwarmMain.load_config()

    # DEFINE BOUNDING BOX(ES)
    cube_min = r_[10, 5, 7, 0]  # cube min vertex
    edge_length = 50.0
    cube = Swarm.Cube(cube_min, edge_length)

    # MAKE SWARM OBJECTS
    # swarm, channel, instrument code (bank, pc)
    swarm_data = [
                    (Swarm.Swarm(7, cube, 6), 1, inst.TRUMPET),
                    (Swarm.Swarm(7, cube, 2), 2, inst.AGOGO),
                    (Swarm.Swarm(7, cube, 1), 3, inst.BLOWN_BOTTLE),
                    # (Swarm.Swarm(7, cube), 9, 0)
    ]
    swarms = list(map(lambda x: x[0], swarm_data))
    manager = Manager(swarms)

    # SET UP MIDI
    midiout = rtmidi.MidiOut().open_port(0)
    seqs = [ChordSequencer(str(i + 1), midiout, swarm_data[i]) for i in range(len(swarm_data))]

    map(lambda x: x.set_tempo(tempo=120), seqs)
    map(lambda x: x.set_scale(scales.min_pen), seqs)

    print("Press Control-C to quit.")

    update = 1/60

    try:
        while True:
            manager.update()
            sleep(update)
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
