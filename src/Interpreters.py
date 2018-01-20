# TODO second go at interpreters cos the old one got very messy
import threading
import json
from time import sleep, time as timenow
from parameters import IP
import scales
import random
from heapq import (heappush, heappop)
from rtmidi.midiconstants import (ALL_SOUND_OFF, BANK_SELECT_MSB, CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)

dynam_axis = 0
pitch_axis = 1
time_axis = 2
length_axis = 3
pan_axis = 4


class PolyInterpreter(threading.Thread):
    """ Uses every boid as a sound source """

    def __init__(self, midiout, swarm_data):
        """
        Make a new interpreter
        """
        super(PolyInterpreter, self).__init__()
        self.midiout = midiout
        self.swarm, self.channel, self.instrument = swarm_data

        # make sure we're targeting the right channel with our MIDI messages
        self.control_change = CONTROL_CHANGE | self.channel
        self.note_on = NOTE_ON | self.channel
        self.program_change = PROGRAM_CHANGE | self.channel

        self.time_elapsed = 0.0

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

        # # TODO temporary chord progression
        # seventh_chord = [0, 4, 7, 10, 12]
        # e7 = list(map(lambda x: x+52, seventh_chord))
        # a7 = list(map(lambda x: x+57, seventh_chord))
        # b7 = list(map(lambda x: x+59, seventh_chord))
        # self.chord_prog = {
        #     0: e7,
        #     1: e7,
        #     2: e7,
        #     3: e7,
        #     4: a7,
        #     5: a7,
        #     6: e7,
        #     7: e7,
        #     8: b7,
        #     9: a7,
        #     10: e7,
        #     11: e7
        # }

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

        self.refresh()

    def refresh(self):
        """ refresh for when params have been changed outside """
        self.set_scale(self.scale)

    def midi_message(self, message):
        """ All MIDI messages sent go through here so they can be logged if needed """
        self.midiout.send_message(message)
        # TODO log if recording
        message.append(self.time_elapsed)
        print(message)

    def play_note(self, pitch, vol):
        """
        Play a note
        :param pitch: midi pitch number
        :param vol: 0-127 volume
        """
        if random.random() < self.probability:
            self.midi_message([self.note_on, pitch, vol])

    def stop_note(self, pitch):
        """ stop a note playing """
        if self.do_note_offs:
            self.midi_message([self.note_on, pitch, 0])

    def activate_instrument(self):
        # (drums are on channel 9)
        if self.channel != 9:
            # bank and program change
            bank, program = self.instrument
            self.midi_message([self.control_change, BANK_SELECT_MSB, bank & 0x7F])
            self.midi_message([self.program_change, program & 0x7F])

    def set_scale(self, scale):
        """
        Set the musical scale for the interpreter
        Assumes lowest pitch is the tonic
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
        self.rhythms = list(reversed([4, 3, 3, 2, 2, 3/2, 1, 1, 1, 1/2, 1/2, 1/2, 1/4]))  # TODO tinker with
        # self.rhythms = [2, 1, 1/2]
        # self.rhythms = [4, 3, 2, 3/2, 1, 1/2, 1/4]
        # self.rhythms = [3/4, 1/4, 3/4, 1/4, 3/4, 1/4, 3/4, 1/4]  # random swing
        self.snap_to_beat = True
        self.interpret_time = self.interpret_time_beat

    def set_time_free(self):
        """ Very dramatic name for a very boring function """
        self.snap_to_beat = False
        self.interpret_time = self.interpret_time_free

    @staticmethod
    def lin_interp(_prop, _min, _range):
        """
        Linear interpolation
        :param _prop: proprtion along the range
        :param _min: value when _prop = 0.0
        :param _range: range from _min
        :return: value somewhere between _min and (_min + _range)
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
        return int(PolyInterpreter.lin_interp(prop, self.dynam_min, self.dynam_range))

    def interpret_pitch(self, prop):
        return int(PolyInterpreter.proportion_along_list(prop, self.notes))

    def interpret_time_beat(self, prop):
        return self.beat * PolyInterpreter.proportion_along_list(prop, self.rhythms)

    def interpret_time_free(self, prop):
        return PolyInterpreter.lin_interp(prop, self.time_min, self.time_range)

    def interpret_pan(self, prop):
        return int(PolyInterpreter.lin_interp(prop, self.pan_min, self.pan_range))

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
        data[length_axis] = data[time_axis] # * pos[length_axis]
        data[pan_axis] = self.interpret_pan(pos[pan_axis])
        return data

    def setup_priority_queue(self, boid_heap, time_elapsed, EVENT_OFF, EVENT_START):
        """ Initialise a queue with the sound agents we will use """
        for boid in self.swarm.boids:
            data = self.interpret(boid.get_loc_ratios())
            self.play_note(data[pitch_axis], data[dynam_axis])
            heappush(boid_heap, (time_elapsed + data[length_axis], (EVENT_OFF, data, boid)))
            heappush(boid_heap, (time_elapsed + data[time_axis], (EVENT_START, data, boid)))

    def parse_priority_queue(self, boid_heap, time_elapsed, EVENT_OFF, EVENT_START):
        """ Parse the data from the head of the queue """
        tag, data, boid = heappop(boid_heap)[1]
        notes_to_play = []

        if tag == EVENT_OFF:
            # stop note
            self.stop_note(data[pitch_axis])
            pass
        elif tag == EVENT_START:
            # interpret next data
            next_data = self.interpret(boid.get_loc_ratios())
            # TODO selective boid playing by options
            self.play_note(next_data[pitch_axis], next_data[dynam_axis])
            # schedule next events
            heappush(boid_heap, (time_elapsed + next_data[length_axis], (EVENT_OFF, next_data, boid)))
            heappush(boid_heap, (time_elapsed + next_data[time_axis], (EVENT_START, next_data, boid)))
            pass
        else:
            print("Unexpected event type:", str(tag))
            pass

        return notes_to_play

    def loop(self):
        """
        The main segement of the run method
        :return:
        """
        # set up priority queue of all the boids to be interpreted
        # time_elapsed = 0.0
        time_step = 0.05
        boid_heap = []
        EVENT_START, EVENT_OFF = 1, 0
        # TODO temp stuff for counting bars, assuming 4/4 time
        counter = 0  # need this because of floating point inaccuracies
        beat = 0
        bars = 0
        timesig = 4  # forced relative to crotchet because this is temp

        self.setup_priority_queue(boid_heap, self.time_elapsed, EVENT_OFF, EVENT_START)

        # TODO add all notes to a list to ensure concurrency (as much as poss)

        # TODO check this definitely does what I want it to do
        while not self.done:

            time_this_loop = timenow()
            notes_to_play = []

            while boid_heap[0][0] <= self.time_elapsed:
                self.parse_priority_queue(boid_heap, self.time_elapsed, EVENT_OFF, EVENT_START)

            time_this_loop = timenow() - time_this_loop
            to_sleep = max(0, time_step - time_this_loop)
            if to_sleep == 0:
                print("OOPS: missed a beat (must be really lagging")

            # # TODO TEMP metronome:
            # if self.snap_to_beat and counter*time_step % self.beat < time_step:
            #     woodblock = 77
            #     beat = (beat+1) % timesig
            #     if beat == 0:
            #         woodblock = 76
            #         bars += 1
            #         bar = bars % len(self.chord_prog.keys())
            #         notes = self.chord_prog[bar]
            #         if self.channel == 0: print("BAR {}".format(bar+1))
            #         # play the chord
            #         # for note in notes:
            #         #     self.midiout.send_message([self.note_on, note, 100])
            #         # TODO change the scale too (assuming chord is base tonic)
            #         degree = (notes[0] % 12) - (self.pitch_min % 12)
            #         new_pitch_min = self.pitch_min + degree
            #         if new_pitch_min < 0:
            #             new_pitch_min += 12
            #         self.pitch_min = new_pitch_min
            #         self.set_scale(self.scale)
            #     if self.channel == 0: print(beat+1)
            #
            #     self.midiout.send_message([NOTE_ON | 9, woodblock, 50])

            sleep(to_sleep)
            self.time_elapsed += time_step
            counter += 1

    def run(self):
        # TODO any necessary setup
        self.loop()
        # finish by stopping all the notes that may still be on
        self.midi_message([self.control_change, ALL_SOUND_OFF, 0])


class MonoInterpreter(PolyInterpreter):
    """ Uses the centre of gravity of the swarm, thus only playing one note at a time """

    def __init__(self, midiout, swarm_data):
        super().__init__(midiout, swarm_data)

    # TODO need to rewrite all the bits that use all the boids and replace them with COM
    def setup_priority_queue(self, boid_heap, time_elapsed, EVENT_OFF, EVENT_START):
        """ Initialise a queue with the sound agents we will use """
        com = self.swarm.get_COM()
        data = self.interpret(com.get_loc_ratios())
        self.play_note(data[pitch_axis], data[dynam_axis])
        heappush(boid_heap, (time_elapsed + data[length_axis], (EVENT_OFF, data, com)))
        heappush(boid_heap, (time_elapsed + data[time_axis], (EVENT_START, data, com)))

    def parse_priority_queue(self, boid_heap, time_elapsed, EVENT_OFF, EVENT_START):
        """ Parse the data from the head of the queue """
        tag, data, com = heappop(boid_heap)[1]

        if tag == EVENT_OFF:
            # stop note
            self.stop_note(data[pitch_axis])
            pass
        elif tag == EVENT_START:
            # interpret next data
            next_data = self.interpret(com.get_loc_ratios())
            self.play_note(next_data[pitch_axis], next_data[dynam_axis])
            # schedule next events
            heappush(boid_heap, (time_elapsed + next_data[length_axis], (EVENT_OFF, next_data, com)))
            heappush(boid_heap, (time_elapsed + next_data[time_axis], (EVENT_START, next_data, com)))
            pass
        else:
            print("Unexpected event type:", str(tag))
            pass
