from abc import ABCMeta, abstractmethod
import threading
from heapq import (heappush, heappop)
from time import sleep
from parameters import IP, SP
from numpy.linalg import norm
import scales
from rtmidi.midiconstants import (ALL_SOUND_OFF, CHANNEL_VOLUME,
                                  CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)


# TODO refactor to make more modular so custom interpreters can be made
# e.g. turning off velocity interpretation, locking to beat, etc

"""
Ideas for more interpreters:

- beat:
    - has a fixed bpm, and time axis dictates note division (much like VelSequencer)
    - maybe velocity allows for slight rubato (so it's the inverse of VelSeq, then)
- scale:
    - pitch axis is "locked" to a scale/mode
"""

dynam_axis = 0
pitch_axis = 1
time_axis = 2


class Interpreter(threading.Thread):
    """
    MIDI output thread
    Interpret the positions of boids as "music"
    """
    __metaclass__ = ABCMeta

    def __init__(self, name, midiout, swarm_data, volume=IP.CHANNEL_VOL):
        super(Interpreter, self).__init__()
        self.name = name  # TODO use or lose
        self.midiout = midiout
        self.swarm = swarm_data[0]
        self.channel = swarm_data[1]
        self.control_change = CONTROL_CHANGE | self.channel
        self.note_on = NOTE_ON | self.channel
        self.instrument = swarm_data[2]
        self.volume = volume
        self.done = False
        self.start()

    def run(self):
        self.activate_instrument(self.instrument)
        self.midiout.send_message([self.control_change, CHANNEL_VOLUME, self.volume & 127])
        # give MIDI instrument some time to activate instrument
        sleep(0.1)
        self.loop()
        self.midiout.send_message([self.control_change, ALL_SOUND_OFF, 0])

    @abstractmethod
    def loop(self):
        pass

    def activate_instrument(self, instrument):
        # (drums are on channel 9)
        if self.channel != 9:
            self.midiout.send_message([PROGRAM_CHANGE | self.channel, instrument & 127])

    @abstractmethod
    def interpret(self, max_v, data):
        """
        :param max_v: the maximum value each data can have
        :param data: list of positional data (x,y,z...)
        :return: the list with the functions applied to each dimension
        """
        pass

    @staticmethod
    def interpret_pitch(max_v, value):
        """
        Default (simple linear interpolation)
        To be overwritten for more complicated interpreters
        Convert positional value into pitch for MIDI
        :param max_v: int, the maximum value <value> can be
        :param value: float, distance along the axis associated with pitch
        :return: int from 21-108 to stay within piano range
        """
        return int((value / max_v) * IP.PITCH_RANGE + IP.PITCH_MIN)

    @staticmethod
    def interpret_time(max_v, value):
        """
        Default (simple linear interpolation)
        To be overwritten for more complicated interpreters
        """
        return (value/max_v) * IP.TIME_RANGE + IP.TIME_MIN

    @staticmethod
    def interpret_dynamic(max_v, value):
        """
        Default (simple linear interpolation)
        To be overwritten for more complicated interpreters
        """
        return int((value/max_v) * IP.DYNAM_RANGE + IP.DYNAM_MIN)


class NaiveSequencer(Interpreter):
    """
    Simple linear interpolation of position of CENTRE OF MASS of each swarm
    """

    def __init__(self, name, midiout, swarm_data, volume=IP.CHANNEL_VOL):
        super().__init__(name, midiout, swarm_data, volume)
        self.snap_to_beat = False
        self.snap_to_scale = False
        self.beat = None
        self.set_beat(on=False)
        self.scale = None
        self.notes = None
        self.set_scale(scales.chrom, on=False)

    def loop(self):
        while not self.done:
            data = self.interpret(self.swarm.cube.edge_length, self.swarm.get_COM().get_location())
            self.midiout.send_message([self.note_on, data[pitch_axis], data[dynam_axis] & 127])
            sleep(max(IP.TIME_MIN, data[time_axis]))
            self.midiout.send_message([self.note_on, data[pitch_axis], 0])

    def set_scale(self, scale, on=True):
        """
        Set the musical scale for the interpreter
        :param scale: a scale from 'scales.py' (in the form of a list of intervals)
        :param on: whether or not to set snap_to_scale to true
        """
        self.scale = scale
        self.notes = scales.gen_range(self.scale, lowest=IP.PITCH_MIN, note_range=IP.PITCH_RANGE)
        self.snap_to_scale = on

    def set_beat(self, beat=IP.TIME_MIN + IP.TIME_RANGE, on=True):
        self.beat = beat
        self.snap_to_beat = on

    def interpret(self, max_v, data):
        """
        :param max_v: the maximum value each data can have
        :param data: list of positional data (x,y,z...)
        :return: the list with the functions applied to each dimension
        """
        dyn = self.interpret_dynamic(max_v, data[dynam_axis])
        if self.snap_to_scale:
            pitch = self.interpret_pitch_scale(max_v, data[pitch_axis], self.notes)
        else:
            pitch = self.interpret_pitch(max_v, data[pitch_axis])
        if self.snap_to_beat:

            time = self.interpret_beat(max_v, data[time_axis], self.beat)
        else:
            time = self.interpret_time(max_v, data[time_axis])

        # TODO hard-coded for 3D
        return [dyn, pitch, time]

    @staticmethod
    def interpret_beat(max_p, boid_p, beat):
        """
        Very similar to VelSequencer.interpret_velocity
        :param max_p: length of time axis
        :param boid_p: boid pos along the time axis
        :param beat: length of 1 beat, seconds
        :return: fraction of <beat>
        """
        boid_p = min(boid_p, max_p)                           # it is possible for the boids to stray past max_p
        proportion = min(0.99, (boid_p / max_p))              # how far along the axis it is (1.0 -> IndexError)
        # TODO spoofing weighted probability:
        divisions = [4, 4, 4, 3, 3, 3, 2, 2, 2, 1, 1, 1, 3/4, 1/2, 1/3, 1/4]
        factor_index = int(proportion // (1/len(divisions)))  # find which note length to use
        # return beat * (divisions[factor_index]/4)

        try:
            return beat * (divisions[factor_index])               # (now treat semibreve as 1) TODO /4 or not?
        except IndexError:
            # TODO this sometimes happens...
            print(boid_p)
            print(max_p)
            print(proportion)
            print(factor_index)
            raise IndexError

    @staticmethod
    def interpret_pitch_scale(max_p, boid_p, notes):
        """
        Pick notes from a list, rather than interpolation
        """
        proportion = boid_p / max_p
        index = int(proportion // (1 / len(notes)))
        return notes[index]


class ChordSequencer(Interpreter):
    """
    Simple linear interpolation of position, but
    treat each boid as a sound agent
    """

    def __init__(self, name, midiout, swarm_data, volume=IP.CHANNEL_VOL):
        super().__init__(name, midiout, swarm_data, volume)

    def loop(self):

        time_elapsed = 0.0
        time_step = 0.1
        boid_heap = []

        # set up the heap with an element for each boid
        for i, boid in enumerate(self.swarm.boids):
            data = self.interpret(self.swarm.cube.edge_length, boid.get_location()) + [i]
            heappush(boid_heap, (time_elapsed + data[time_axis], data))

        while not self.done:

            # print(time_elapsed)

            # TODO test properly...
            # stop the notes that have ended and load the next ones
            while boid_heap[0][0] <= time_elapsed:
                data = heappop(boid_heap)[1]
                pitch = max(0, data[pitch_axis]) & 127
                self.midiout.send_message([self.note_on, pitch, 0])
                boid_index = data[-1]
                next_data = self.interpret(self.swarm.cube.edge_length,
                                           self.swarm.boids[boid_index].get_location()) + [boid_index]
                # play the new note
                new_pitch = max(0, next_data[pitch_axis]) & 127
                self.midiout.send_message([self.note_on, new_pitch, data[dynam_axis] & 127])
                # add to the heap so it can be turned off when it's done
                heappush(boid_heap, (time_elapsed + next_data[time_axis], next_data))

            # finally, enforce time step
            sleep(time_step)
            time_elapsed += time_step

            # print(boid_heap)
            # assert len(boid_heap) == len(self.swarm.boids)

    def interpret(self, max_v, data):
        """
        :param max_v: the maximum value each data can have
        :param data: list of positional data (x,y,z...)
        :return: the list with the functions applied to each dimension
        """
        # TODO hard-coded for 3D
        return [self.interpret_dynamic(max_v, data[dynam_axis]),
                self.interpret_pitch(max_v, data[pitch_axis]),
                self.interpret_time(max_v, data[time_axis])]


class VelSequencer(NaiveSequencer):
    """
    Note length is a function of velocity of boids
    Otherwise identical to Naive
    """
    def loop(self):

        while not self.done:
            com = self.swarm.get_COM()
            data = self.interpret(self.swarm.cube.edge_length, com.get_location())
            note_length = self.interpret_velocity(SP.MAX_SPEED, com.velocity, data[time_axis])
            self.midiout.send_message([self.note_on, data[pitch_axis], data[dynam_axis] & 127])
            sleep(max(IP.TIME_MIN, note_length))
            self.midiout.send_message([self.note_on, data[pitch_axis], 0])

    @staticmethod
    def interpret_velocity(max_vel, boid_vel, time):
        """
        The faster the boid goes, the more we subdivide the predetermined note length
        :param max_vel: the fastest a boid can go
        :param boid_vel: how fast it is going
        :param time: the interpreted time value of the boid
        :return:
        """
        pro_v = norm(boid_vel)/max_vel                   # proportion of max speed
        divisions = [4, 2, 1, 3/4, 1/2, 1/3, 1/4]        # note lengths (1 is "crotchet" equivalent for readability)
        factor_index = int(pro_v // (1/len(divisions)))  # find which note length to use
        return time * (divisions[factor_index]/4)        # (now treat semibreve as 1)