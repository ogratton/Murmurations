from abc import ABCMeta, abstractmethod
import threading
from heapq import (heappush, heappop)
from time import sleep
from parameters import IP, SP
from numpy.linalg import norm
from rtmidi.midiconstants import (ALL_SOUND_OFF, CHANNEL_VOLUME,
                                  CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)


"""
Ideas for more interpreters:

- drummer:
    - has a fixed bpm, and time axis dictates note division (much like VelSequencer)
    - maybe velocity allows for slight rubato (so it's the inverse of VelSeq, then)
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
        self.name = name  # TODO do something with it or remove it
        self.midiout = midiout
        self.swarm = swarm_data[0]
        self.channel = swarm_data[1]
        self.cc = CONTROL_CHANGE | self.channel
        self.no = NOTE_ON | self.channel
        self.instrument = swarm_data[2]
        self.volume = volume
        self.done = False
        self.start()

    @abstractmethod
    def run(self):
        pass

    def run_dec(self):
        """
        Decorator for run method (common start and end behaviour)
        """
        def decorated(f):
            def wrapper(*args, **kwargs):
                self.activate_instrument(self.instrument)
                self.midiout.send_message([self.cc, CHANNEL_VOLUME, self.volume & 127])
                # give MIDI instrument some time to activate instrument
                sleep(0.1)
                f(*args, **kwargs)
                self.midiout.send_message([self.cc, ALL_SOUND_OFF, 0])
            return wrapper
        return decorated

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

    def run(self):

        @self.run_dec()
        def loop():
            while not self.done:
                data = self.interpret(self.swarm.cube.edge_length, self.swarm.get_COM().get_location())
                self.midiout.send_message([NOTE_ON | self.channel, data[pitch_axis], data[dynam_axis] & 127])
                sleep(max(IP.TIME_MIN, data[time_axis]))
                self.midiout.send_message([NOTE_ON | self.channel, data[pitch_axis], 0])

        loop()

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


class ChordSequencer(Interpreter):
    """
    Simple linear interpolation of position, but
    treat each boid as a sound agent
    """

    def __init__(self, name, midiout, swarm_data, volume=IP.CHANNEL_VOL):
        super().__init__(name, midiout, swarm_data, volume)

    def run(self):

        @self.run_dec()
        def loop():
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
                    self.midiout.send_message([self.no, pitch, 0])
                    boid_index = data[-1]
                    next_data = self.interpret(self.swarm.cube.edge_length,
                                               self.swarm.boids[boid_index].get_location()) + [boid_index]
                    # play the new note
                    new_pitch = max(0, next_data[pitch_axis]) & 127
                    self.midiout.send_message([self.no, new_pitch, data[dynam_axis] & 127])
                    # add to the heap so it can be turned off when it's done
                    heappush(boid_heap, (time_elapsed + next_data[time_axis], next_data))

                # finally, enforce time step
                sleep(time_step)
                time_elapsed += time_step

                # print(boid_heap)
                # assert len(boid_heap) == len(self.swarm.boids)

        loop()

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
    """
    def run(self):

        @self.run_dec()
        def loop():
            while not self.done:
                com = self.swarm.get_COM()
                data = self.interpret(self.swarm.cube.edge_length, com.get_location())
                note_length = self.interpret_velocity(SP.MAX_SPEED, com.velocity, data[time_axis])
                self.midiout.send_message([NOTE_ON | self.channel, data[pitch_axis], data[dynam_axis] & 127])
                sleep(max(IP.TIME_MIN, note_length))
                self.midiout.send_message([NOTE_ON | self.channel, data[pitch_axis], 0])

        loop()

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
