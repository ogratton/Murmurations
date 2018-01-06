# TODO second go at interpreters cos the old one got very messy
import threading
from parameters import IP
import scales
import random
from heapq import (heappush, heappop)
from rtmidi.midiconstants import (ALL_SOUND_OFF, BANK_SELECT_MSB,
                                  CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)


class NewInterpreter(threading.Thread):

    def __init__(self, midiout, swarm_data):
        """
        Make a new interpreter
        """
        super(NewInterpreter, self).__init__()
        self.midiout = midiout
        self.swarm, self.channel, self.instrument = swarm_data

        # make sure we're targeting the right channel with our MIDI messages
        self.control_change = CONTROL_CHANGE | self.channel
        self.note_on = NOTE_ON | self.channel
        self.program_change = PROGRAM_CHANGE | self.channel

        # SET DEFAULTS
        self.pitch_range = IP.PITCH_RANGE
        self.pitch_min = IP.PITCH_MIN
        self.dynam_range = IP.DYNAM_RANGE
        self.dynam_min = IP.DYNAM_MIN
        self.time_range = IP.TIME_RANGE
        self.time_min = IP.TIME_MIN
        self.probability = IP.PROBABILITY
        self.scale = None
        self.notes = None
        self.range = 0
        self.set_scale(scales.chrom)
        self.beat = None
        self.rhythms = None
        self.snap_to_beat = False
        self.interpret_time = self.interpret_time_free
        self.activate_instrument()

        self.done = False
        self.start()

    def play_note(self, info):
        """
        Play a note
        :param info: a list of midi parameters to be sent to midiout
        """
        if random.random() < self.probability:
            self.midiout.send_message(info)

    def activate_instrument(self):
        # (drums are on channel 9)
        if self.channel != 9:
            # bank and program change
            bank, program = self.instrument
            self.midiout.send_message([self.control_change, BANK_SELECT_MSB, bank & 0x7F])
            self.midiout.send_message([self.program_change, program & 127])

    def set_scale(self, scale):
        """
        Set the musical scale for the interpreter
        :param scale: a scale from 'scales.py' (in the form of a list of intervals)
        """
        self.scale = scale
        self.notes = scales.gen_range(self.scale, lowest=self.pitch_min, note_range=self.pitch_range)
        self.range = len(self.notes)

    def set_tempo(self, beats_per_min):
        """
        Set the length in seconds of a single beat
        Also turns on beat snapping
        :param beats_per_min:
        :return:
        """
        self.beat = 60 / beats_per_min
        self.rhythms = [4, 3, 2, 3/2, 1, 1/2, 1/4, 1/8]  # TODO tinker with
        self.snap_to_beat = True
        self.interpret_time = self.interpret_time_beat  # TODO need way to switch back if live GUI made

    @staticmethod
    def lin_interp(_prop, _min, _range):
        """
        Linear interpolation
        :param _prop: proprtion along the range
        :param _min: value when _prop = 0.0
        :param _range: range from _min
        :return: value somewhere between _min and (_min+_range)
        """
        return _prop * _range + _min

    @staticmethod
    def proportion_along_list(prop, lst):
        """
        Convert a proportion into an index of a list
        e.g. 0.5 will return the middle element of the list
        :param prop: proportion needed along the list
        :param lst: the list to use
        :return:
        """
        index = int(prop * len(lst))
        return lst[index]

    # DIMENSION-SPECIFIC INTERPRETATION FUNCTIONS

    def interpret_dynam(self, prop):
        return NewInterpreter.lin_interp(prop, self.dynam_min, self.dynam_range)

    def interpret_pitch(self, prop):
        return NewInterpreter.proportion_along_list(prop, self.notes)

    def interpret_time_beat(self, prop):
        return NewInterpreter.proportion_along_list(prop, self.rhythms)

    def interpret_time_free(self, prop):
        return NewInterpreter.lin_interp(prop, self.time_min, self.time_range)

    def interpret(self, pos):
        """
        Convert the position of a boid into music parameters
        :param pos: ratios of how far along the axis the boid is in each dimension
        :return:
        """
        # TODO
        loudness = NewInterpreter.lin_interp(pos[0], self.dynam_min, self.dynam_range)
        pitch = NewInterpreter.proportion_along_list(pos[1], self.notes)
        event_length = 0
        pan = 0
        return []

    def loop(self):
        """
        The main segement of the run method
        :return:
        """
        # set up priority queue of all the boids to be interpreted
        time_elapsed = 0.0
        time_step = 0.1
        boid_heap = []
        # TODO
        for boid in self.swarm.boids:
            data = self.interpret(boid.get_loc_ratios())
            heappush(boid_heap, (time_elapsed, data))

        while not self.done:
            # TODO
            pass

    def run(self):
        # TODO any necessary setup
        self.loop()
        # finish by stopping all the notes that may still be on
        self.midiout.send_message([self.control_change, ALL_SOUND_OFF, 0])
