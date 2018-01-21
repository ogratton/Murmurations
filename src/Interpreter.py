""" DEPRECATED """

from abc import ABCMeta, abstractmethod
import threading
import json
from heapq import (heappush, heappop)
from random import random
from time import sleep
from Parameters import IP
from numpy.linalg import norm
import Scales
from rtmidi.midiconstants import (ALL_SOUND_OFF, BANK_SELECT_MSB,
                                  CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE, PAN)


# TODO refactor to make more modular so custom interpreters can be made
# e.g. turning off velocity interpretation, locking to beat, etc

"""
Ideas for more interpreters:

- beat:
    - has a fixed bpm, and time axis dictates note division (much like VelSequencer)
    - maybe velocity allows for slight rubato (so it's the inverse of VelSeq, then)
- gravity:
    - treat attractors as gravity wells
    - boids speed up as they get closer
    - end up orbiting them (creates interest when attractor doesn't change)
- probabilistic:
    - based on Chord, but boids only have a *probability* to play at each update
"""

dynam_axis = 0
pitch_axis = 1
time_axis = 2
pan_axis = 3


class Interpreter(threading.Thread):
    """
    MIDI output thread
    Interpret the positions of boids as "music"
    """
    __metaclass__ = ABCMeta

    def __init__(self, midiout, swarm_data):
        super(Interpreter, self).__init__()
        self.midiout = midiout
        self.swarm = swarm_data[0]
        self.channel = swarm_data[1]
        self.control_change = CONTROL_CHANGE | self.channel
        self.note_on = NOTE_ON | self.channel
        self.instrument = swarm_data[2]

        # SET DEFAULTS
        self.pitch_range = IP.PITCH_RANGE
        self.pitch_min = IP.PITCH_MIN
        self.dynam_range = IP.DYNAM_RANGE
        self.dynam_min = IP.DYNAM_MIN
        self.time_range = IP.TIME_RANGE
        self.time_min = IP.TIME_MIN
        self.probability = IP.PROBABILITY

        self.done = False
        self.start()

    def setup_interp(self, json_file):
        """
        Allows parameters to be set from JSON format
        :param json_file:
        :return:
        """
        data = json.load(open(json_file))

        for d in data.items():
            if d[0] == 'pitch_min':
                self.pitch_min = d[1]
            elif d[0] == 'pitch_range':
                self.pitch_range = d[1]
            elif d[0] == 'dynam_min':
                self.dynam_min = d[1]
            elif d[0] == 'dynam_range':
                self.dynam_range = d[1]
            elif d[0] == 'time_min':
                self.time_min = d[1]
            elif d[0] == 'time_range':
                self.time_range = d[1]
            elif d[0] == 'probability':
                self.probability = d[1]
            else:
                print("Unexpected parameter: {}".format(d[0]))

        self.refresh()

    def refresh(self):
        """ Reset parameters that depend on others, and the like """
        pass

    def run(self):
        self.activate_instrument()
        # TODO this must be done before every message out if it is to have effect
        # give MIDI instrument some time to activate instrument
        sleep(0.1)
        self.loop()
        self.midiout.send_message([self.control_change, ALL_SOUND_OFF, 0])

    @abstractmethod
    def loop(self):
        pass

    def activate_instrument(self):
        # (drums are on channel 9)
        if self.channel != 9:
            # bank and program change
            bank, program = self.instrument
            self.midiout.send_message([self.control_change, BANK_SELECT_MSB, bank & 0x7F])
            self.midiout.send_message([PROGRAM_CHANGE | self.channel, program & 127])

    def backwards_interpret(self, message, time):
        """
        Convert a midi input message to boid-space
        :param message: e.g. [144,47,120] (i.e. note on, B3, loud)
        :param time: in seconds, since last midi-in message
        """
        # proportion along the axes (default middle)
        pitch_space = 0.5
        dynam_space = 0.5
        time_space = 0.5

        pmin, pran = self.pitch_min, self.pitch_range
        dmin, dran = self.dynam_min, self.dynam_range
        tmin, tran = self.time_min, self.time_range  # TODO note that these are not used when beat is on

        # note on messages
        if message[0] in range(144, 160):

            # DEBUG: PLAY THE INCOMING MESSAGE
            # self.midiout.send_message([self.note_on, message[1], message[2]])

            # TODO should account for the scale and take note of "wrong" notes
            if message[1] in range(pmin, pmin+pran+1):
                pitch_space = (message[1]-pmin)/pran
            else:
                print("need something smarter for pitch: {0}".format(message[1]))

            dval = max(min(dmin+dran+1, message[2]), dmin)
            dynam_space = (dval - dmin) / dran

            if tmin <= time <= tmin+tran:
                time_space = (time-tmin)/tran
            else:
                print("need something smarter for time: {0}".format(time))

        self.swarm.place_attractor([dynam_space, pitch_space, time_space])

    @abstractmethod
    def interpret(self, max_v, data):
        """
        :param max_v: the maximum value each data can have (cube edge length)
        :param data: list of positional data (x,y,z...)
        :return: the list with the functions applied to each dimension
        """
        # TODO error catching on all these
        pass

    def interpret_pitch(self, max_v, value):
        """
        Default (simple linear interpolation)
        To be overwritten for more complicated interpreters
        Convert positional value into pitch for MIDI
        :param max_v: int, the maximum value <value> can be
        :param value: float, distance along the axis associated with pitch
        :return: int from 21-108 to stay within piano range
        """
        # TODO obsolete now you can just use the chromatic scale with interpret_pitch_scale
        return int((value / max_v) * self.pitch_range + self.pitch_min)

    @staticmethod
    def interpret_pitch_scale(max_p, boid_p, notes):
        """
        Pick notes from a list, rather than interpolation
        """
        proportion = max(0.01, min(0.99, boid_p / max_p))
        index = int(proportion * len(notes))
        return notes[index]

    def interpret_time(self, max_v, value):
        """
        Default (simple linear interpolation)
        To be overwritten for more complicated interpreters
        """
        return (value/max_v) * self.time_range + self.time_min

    def interpret_dynamic(self, max_v, value):
        """
        Default (simple linear interpolation)
        To be overwritten for more complicated interpreters
        """
        return int((value/max_v) * self.dynam_range + self.dynam_min)

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
        proportion = max(0.01, min(0.99, (boid_p / max_p)))   # how far along the axis it is (1.0 -> IndexError)
        # TODO decide on what to put in this list
        # triplets and stuff
        divisions = [4, 3, 2, 3/2, 1, 1/2, 1/4, 1/8]
        # divisions = [1, 3/4, 1/2, 1/3, 1/4]
        factor_index = int(proportion // (1/len(divisions)))  # find which note length to use

        # print(beat * (divisions[factor_index]/4))

        return beat * (divisions[factor_index])               # TODO /4 or not?


class ChordSequencer(Interpreter):
    """
    Simple linear interpolation of position of each boid
    """

    def __init__(self, midiout, swarm_data):
        super().__init__(midiout, swarm_data)
        self.snap_to_beat = False
        self.snap_to_scale = False
        self.beat = None
        self.set_tempo(on=False)
        self.scale = None
        self.notes = None
        self.set_scale(Scales.chrom, on=True)

    def loop(self):

        time_elapsed = 0.0
        time_step = 0.1
        boid_heap = []

        # set up the heap with an element for each boid
        # TODO could use boid.id (though that is probably slower)
        for boid in self.swarm.boids:
            data = self.interpret(self.swarm.cube.edge_length, boid.get_location()) + [boid.id]
            # play the note:
            new_pitch = max(0, data[pitch_axis]) & 127
            new_dynam = max(0, data[dynam_axis]) & 127
            if random() < self.probability:
                self.midiout.send_message([self.note_on, new_pitch, new_dynam])
            # add to the priority queue
            # heapq: (abs time, note data)
            heappush(boid_heap, (time_elapsed + data[time_axis], data))

        while not self.done:

            # TODO test properly... and maybe account for computation time
            # stop the notes that have ended and load the next ones
            while boid_heap[0][0] <= time_elapsed:

                data = heappop(boid_heap)[1]
                pitch = data[pitch_axis] & 127
                self.midiout.send_message([self.note_on, pitch, 0])
                boid_index = data[-1]
                next_data = self.interpret(self.swarm.cube.edge_length,
                                           self.swarm.boids[boid_index].get_location()) + [boid_index]
                # play the new note
                new_pitch = max(0, next_data[pitch_axis]) & 127
                new_dynam = max(0, next_data[dynam_axis]) & 127
                new_time = time_elapsed + next_data[time_axis]

                # TODO use 4th dimension properly
                pan_val = data[pan_axis]
                self.midiout.send_message([self.control_change, PAN, pan_val & 0x7F])

                # TODO playing on probability
                if random() < self.probability:
                    self.midiout.send_message([self.note_on, new_pitch, new_dynam])
                # add to the heap so it can be turned off when it's done
                heappush(boid_heap, (new_time, next_data))

            # finally, enforce time step
            sleep(time_step)
            time_elapsed += time_step

            # print(boid_heap)
            # assert len(boid_heap) == len(self.swarm.boids)

    def refresh(self):
        self.set_scale(self.scale)
        self.set_tempo()

    def set_scale(self, scale, on=True):
        """
        Set the musical scale for the interpreter
        :param scale: a scale from 'Scales.py' (in the form of a list of intervals)
        :param on: whether or not to set snap_to_scale to true
        """
        self.scale = scale
        self.notes = Scales.gen_range(self.scale, lowest=self.pitch_min, note_range=self.pitch_range)
        self.snap_to_scale = on

    def set_tempo(self, tempo=None, on=True):
        """
        Set tempo
        :param tempo: float, e.g. crotchet=120.0
        :param on: whether or not to use this tempo
        :return:
        """
        # note on python:
        # default value must be set in the body, otherwise it will take the value as it is on run-time

        if tempo is None:
            self.beat = self.time_min + self.time_range
        else:
            self.beat = (60 / tempo) * 4  # crotchet = 120, so semibreve is 2 seconds

        self.snap_to_beat = on

    def interpret(self, max_v, data):
        """
        :param max_v: the maximum value each data can have (cube edge length)
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

        # TODO knock-off pan interpolater
        pan_min = 30
        pan_range = 67
        pan = int(pan_range * data[pan_axis] / max_v) + pan_min

        # TODO hard-coded for 3D
        return [dyn, pitch, time, pan]


class VelSequencer(ChordSequencer):
    """
    Note length is a function of velocity of boids
    """
    def loop(self):
        # TODO
        pass

    @staticmethod
    def interpret_velocity(max_vel, boid_vel, time=1):
        """
        The faster the boid goes, the more we subdivide the predetermined note length
        :param max_vel: the fastest a boid can go
        :param boid_vel: how fast it is going
        :param time: the interpreted time value of the boid
        :return:
        """
        # TODO: the boids spend a lot more of their time in the extremes of their speed limit than they do
        # in the extremes of the z axis, so the divisions list has been cut down significantly

        pro_v = min(0.99, norm(boid_vel)/max_vel)                   # proportion of max speed
        divisions = [4, 3, 2, 1]        # note lengths (1 is "crotchet" equivalent for readability)
        factor_index = int(pro_v // (1/len(divisions)))  # find which note length to use

        print(time * (divisions[factor_index]/4))

        return time * (divisions[factor_index]/4)        # (now treat semibreve as 1)
