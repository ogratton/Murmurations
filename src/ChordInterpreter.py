from heapq import (heappush, heappop)
import Swarm
import PYGAMESwarmRender
import rtmidi
from numpy import r_
import threading
from time import sleep
from rtmidi.midiconstants import (ALL_SOUND_OFF, CHANNEL_VOLUME,
                                  CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)

# TODO merge this with Naive with a nice abstract class or something - they needn't be separate

"""
Interpret each boid as a musical note
"""

# CONSTANTS

pitch_range = 40    # 88   - 88 keys on a piano, so seems suitable
pitch_min = 30      # 21   - A0
time_range = 1.5   # 1    - range in time between events
time_min = 0.5     # 0.05 - min time between events
dynam_max = 127     # 127  - max dynamic
dynam_min = 25      # 0    - min dynamic
dynam_range = dynam_max - dynam_min

dynam_axis = 0
pitch_axis = 1
time_axis = 2


class ChordSequencer(threading.Thread):
    """MIDI output thread."""

    def __init__(self, name, midiout, swarm_data, volume=127):
        super(ChordSequencer, self).__init__()
        self.name = name  # TODO
        self.midiout = midiout
        self.swarm = swarm_data[0]
        self.channel = swarm_data[1]
        self.instrument = swarm_data[2]
        self.volume = volume
        self.done = False
        self.start()

    def run(self):
        self.activate_instrument(self.instrument)
        cc = CONTROL_CHANGE | self.channel
        self.midiout.send_message([cc, CHANNEL_VOLUME, self.volume & 0x7F])

        # give MIDI instrument some time to activate instrument
        sleep(0.3)

        time_elapsed = 0.0
        time_step = 0.1
        boid_heap = []

        # set up the heap with an element for each boid
        for i, boid in enumerate(self.swarm.boids):
            data = interpret(self.swarm.cube.edge_length, boid.location) + [i]
            heappush(boid_heap, (time_elapsed + data[time_axis], data))

        while not self.done:

            # print(time_elapsed)

            # stop the notes that have ended and load the next ones
            while boid_heap[0][0] <= time_elapsed:
                data = heappop(boid_heap)[1]
                self.midiout.send_message([NOTE_ON | self.channel, data[pitch_axis], 0])
                boid_index = data[-1]
                next_data = interpret(self.swarm.cube.edge_length, self.swarm.boids[boid_index].location) + [boid_index]
                # play the new note
                self.midiout.send_message([NOTE_ON | self.channel, next_data[pitch_axis], data[dynam_axis] & 127])
                # add to the heap so it can be turned off when it's done
                heappush(boid_heap, (time_elapsed + next_data[time_axis], next_data))

            # finally, enforce time step
            sleep(time_step)
            time_elapsed += time_step

            # print(boid_heap)

            # assert len(boid_heap) == len(self.swarm.boids)

        self.midiout.send_message([cc, ALL_SOUND_OFF, 0])

    def activate_instrument(self, instrument):
        # (drums are one channel 9)
        if self.channel != 9:
            self.midiout.send_message([PROGRAM_CHANGE | self.channel, instrument & 0x7F])


def interpret(max_v, data):
    """
    :param max_v: the maximum value each data can have
    :param data: list of positional data (x,y,z...)
    :return: the list with the functions applied to each dimension
    """
    # TODO hard-coded for 3D
    return [interpret_dynamic(max_v, data[0]),
            interpret_pitch(max_v, data[1]),
            interpret_time(max_v, data[2])]


def interpret_pitch(max_v, value):
    """
    Convert positional value into pitch for MIDI
    :param max_v: int, the maximum value <value> can be
    :param value: float, distance along the axis associated with pitch
    :return: int from 21-108 to stay within piano range
    """
    return int((value / max_v) * pitch_range + pitch_min)


def interpret_time(max_v, value):
    return (value/max_v) * time_range + time_min


def interpret_dynamic(max_v, value):
    return int((value/max_v) * dynam_range + dynam_min)


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
            NaiveSequencer('3', midiout, swarm_data[2]),
            NaiveSequencer('4', midiout, swarm_data[3])]

    print("Playing random shit. Press Control-C to quit.")

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
