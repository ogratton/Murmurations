from abc import ABCMeta, abstractmethod
import threading
from heapq import (heappush, heappop)
from time import sleep
from parameters import IP
from rtmidi.midiconstants import (ALL_SOUND_OFF, CHANNEL_VOLUME,
                                  CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)

dynam_axis = 0
pitch_axis = 1
time_axis = 2


class Interpreter(threading.Thread):
    __metaclass__ = ABCMeta

    def __init__(self, name, midiout, swarm_data, volume=IP.CHANNEL_VOL):
        super(Interpreter, self).__init__()
        self.name = name  # TODO do something with it or remove it
        self.midiout = midiout
        self.swarm = swarm_data[0]
        self.channel = swarm_data[1]
        self.instrument = swarm_data[2]
        self.volume = volume
        self.done = False
        self.start()

    @abstractmethod
    def run(self):
        pass

    def activate_instrument(self, instrument):
        # (drums are on channel 9)
        if self.channel != 9:
            self.midiout.send_message([PROGRAM_CHANGE | self.channel, instrument & 0x7F])

    @abstractmethod
    def interpret(self, max_v, data):
        """
        :param max_v: the maximum value each data can have
        :param data: list of positional data (x,y,z...)
        :return: the list with the functions applied to each dimension
        """
        pass

class ChordSequencer(Interpreter):
    """MIDI output thread."""

    def __init__(self, name, midiout, swarm_data, volume=IP.CHANNEL_VOL):
        super().__init__(name, midiout, swarm_data, volume)

    def run(self):
        self.activate_instrument(self.instrument)
        cc = CONTROL_CHANGE | self.channel
        self.midiout.send_message([cc, CHANNEL_VOLUME, self.volume & 0x7F])

        # give MIDI instrument some time to activate instrument
        sleep(0.1)

        time_elapsed = 0.0
        time_step = 0.05
        boid_heap = []

        # set up the heap with an element for each boid
        for i, boid in enumerate(self.swarm.boids):
            data = self.interpret(self.swarm.cube.edge_length, boid.location) + [i]
            heappush(boid_heap, (time_elapsed + data[time_axis], data))

        while not self.done:

            # print(time_elapsed)

            # stop the notes that have ended and load the next ones
            while boid_heap[0][0] <= time_elapsed:
                data = heappop(boid_heap)[1]
                self.midiout.send_message([NOTE_ON | self.channel, data[pitch_axis], 0])
                boid_index = data[-1]
                next_data = self.interpret(self.swarm.cube.edge_length, self.swarm.boids[boid_index].location) + [boid_index]
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

    def interpret(self, max_v, data):
        """
        :param max_v: the maximum value each data can have
        :param data: list of positional data (x,y,z...)
        :return: the list with the functions applied to each dimension
        """
        # TODO hard-coded for 3D
        return [self.interpret_dynamic(max_v, data[0]),
                self.interpret_pitch(max_v, data[1]),
                self.interpret_time(max_v, data[2])]

    @staticmethod
    def interpret_pitch(max_v, value):
        """
        Convert positional value into pitch for MIDI
        :param max_v: int, the maximum value <value> can be
        :param value: float, distance along the axis associated with pitch
        :return: int from 21-108 to stay within piano range
        """
        return int((value / max_v) * IP.PITCH_RANGE + IP.PITCH_MIN)

    @staticmethod
    def interpret_time(max_v, value):
        return (value/max_v) * IP.TIME_RANGE + IP.TIME_MIN

    @staticmethod
    def interpret_dynamic(max_v, value):
        return int((value/max_v) * IP.DYNAM_RANGE + IP.DYNAM_MIN)


class NaiveSequencer(Interpreter):
    """MIDI output thread."""

    def __init__(self, name, midiout, swarm_data, volume=IP.CHANNEL_VOL):
        super().__init__(name, midiout, swarm_data, volume)

    def run(self):
        self.activate_instrument(self.instrument)
        cc = CONTROL_CHANGE | self.channel
        self.midiout.send_message([cc, CHANNEL_VOLUME, self.volume & 0x7F])

        # give MIDI instrument some time to activate instrument
        sleep(0.1)

        while not self.done:
            data = self.interpret(self.swarm.cube.edge_length, self.swarm.get_COM().get_location())
            self.midiout.send_message([NOTE_ON | self.channel, data[1], data[0] & 127])
            sleep(max(IP.TIME_MIN, data[2]))
            self.midiout.send_message([NOTE_ON | self.channel, data[1], 0])

        self.midiout.send_message([cc, ALL_SOUND_OFF, 0])

    def interpret(self, max_v, data):
        """
        :param max_v: the maximum value each data can have
        :param data: list of positional data (x,y,z...)
        :return: the list with the functions applied to each dimension
        """
        # TODO hard-coded for 3D
        return [self.interpret_dynamic(max_v, data[0]),
                self.interpret_pitch(max_v, data[1]),
                self.interpret_time(max_v, data[2])]

    @staticmethod
    def interpret_pitch(max_v, value):
        """
        Convert positional value into pitch for MIDI
        :param max_v: int, the maximum value <value> can be
        :param value: float, distance along the axis associated with pitch
        :return: int from 21-108 to stay within piano range
        """
        return int((value / max_v) * IP.PITCH_RANGE + IP.PITCH_MIN)

    @staticmethod
    def interpret_time(max_v, value):
        return (value/max_v) * IP.TIME_RANGE + IP.TIME_MIN

    @staticmethod
    def interpret_dynamic(max_v, value):
        return int((value/max_v) * IP.DYNAM_RANGE + IP.DYNAM_MIN)
