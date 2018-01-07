# TODO second go at interpreters cos the old one got very messy
import threading
import json
from time import sleep, time as timenow
from parameters import IP
import scales
import random
from heapq import (heappush, heappop)
from rtmidi.midiconstants import (ALL_SOUND_OFF, BANK_SELECT_MSB,
                                  CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)

dynam_axis = 0
pitch_axis = 1
time_axis = 2
length_axis = 3
pan_axis = 4


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
        self.dims = self.swarm.dims
        self.pitch_range = IP.PITCH_RANGE
        self.pitch_min = IP.PITCH_MIN
        self.dynam_range = IP.DYNAM_RANGE
        self.dynam_min = IP.DYNAM_MIN
        self.time_range = IP.TIME_RANGE
        self.time_min = IP.TIME_MIN
        self.pan_range = IP.PAN_RANGE
        self.pan_min = IP.PAN_MIN
        self.probability = IP.PROBABILITY
        self.do_note_offs = 1
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
            elif d[0] == 'note_offs':
                self.do_note_offs = d[1]
            else:
                print("Unexpected parameter: {}".format(d[0]))

    def refresh(self):
        """ refresh for when params have been changed outside """
        self.set_scale(self.scale)

    def play_note(self, pitch, vol):
        """
        Play a note
        :param pitch: midi pitch number
        :param vol: 0-127 volume
        """
        if random.random() < self.probability:
            self.midiout.send_message([self.note_on, pitch, vol])

    def stop_note(self, pitch):
        """ stop a note playing """
        if self.do_note_offs:
            self.midiout.send_message([self.note_on, pitch, 0])

    def activate_instrument(self):
        # (drums are on channel 9)
        if self.channel != 9:
            # bank and program change
            bank, program = self.instrument
            self.midiout.send_message([self.control_change, BANK_SELECT_MSB, bank & 0x7F])
            self.midiout.send_message([self.program_change, program & 0x7F])

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
        return int(NewInterpreter.lin_interp(prop, self.dynam_min, self.dynam_range))

    def interpret_pitch(self, prop):
        return int(NewInterpreter.proportion_along_list(prop, self.notes))

    def interpret_time_beat(self, prop):
        return self.beat * NewInterpreter.proportion_along_list(prop, self.rhythms)

    def interpret_time_free(self, prop):
        return NewInterpreter.lin_interp(prop, self.time_min, self.time_range)

    def interpret_pan(self, prop):
        return int(NewInterpreter.lin_interp(prop, self.pan_min, self.pan_range))

    def interpret(self, pos):
        """
        Convert the position of a boid into music parameters
        :param pos: ratios of how far along the axis the boid is in each dimension
        :return:
        """
        data = [-1] * self.dims
        data[dynam_axis] = self.interpret_dynam(pos[dynam_axis])
        data[pitch_axis] = self.interpret_pitch(pos[pitch_axis])
        data[time_axis] = self.interpret_time(pos[time_axis])
        data[length_axis] = pos[length_axis] * data[time_axis]
        data[pan_axis] = self.interpret_pan(pos[pan_axis])
        return data

    def loop(self):
        """
        The main segement of the run method
        :return:
        """
        # set up priority queue of all the boids to be interpreted
        time_elapsed = 0.0
        time_step = 0.05
        boid_heap = []
        EVENT_START, EVENT_OFF = 0, 1

        for boid in self.swarm.boids:
            data = self.interpret(boid.get_loc_ratios())
            self.play_note(data[pitch_axis], data[dynam_axis])
            heappush(boid_heap, (time_elapsed + data[length_axis], (EVENT_OFF, data, boid)))
            heappush(boid_heap, (time_elapsed + data[time_axis], (EVENT_START, data, boid)))

        # TODO I am 90% sure I've ballsed this up somewhere
        while not self.done:

            time_this_loop = timenow()

            while boid_heap[0][0] <= time_elapsed:
                tag, data, boid = heappop(boid_heap)[1]

                if tag == EVENT_OFF:
                    # stop note
                    self.stop_note(data[pitch_axis])
                    pass
                elif tag == EVENT_START:
                    # interpret next data
                    next_data = self.interpret(boid.get_loc_ratios())
                    self.play_note(next_data[pitch_axis], next_data[dynam_axis])
                    # schedule next events
                    heappush(boid_heap, (time_elapsed + next_data[length_axis], (EVENT_OFF, next_data, boid)))
                    heappush(boid_heap, (time_elapsed + next_data[time_axis], (EVENT_START, next_data, boid)))
                    pass
                else:
                    print("Unexpected event type:", str(tag))
                    pass

            time_this_loop = timenow() - time_this_loop
            to_sleep = max(0, time_step - time_this_loop)
            if to_sleep == 0:
                print("oh dear")
            sleep(to_sleep)
            time_elapsed += time_step

    def run(self):
        # TODO any necessary setup
        self.loop()
        # finish by stopping all the notes that may still be on
        self.midiout.send_message([self.control_change, ALL_SOUND_OFF, 0])
