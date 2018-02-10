import threading
import json
from time import sleep, time as timenow

# for logs
from datetime import datetime
import csv

from Parameters import IP, SP
import Scales
import Instruments
import random
from heapq import (heappush, heappop)
from rtmidi.midiconstants import (ALL_SOUND_OFF, BANK_SELECT_MSB, CONTROL_CHANGE,
                                  NOTE_ON, NOTE_OFF, PROGRAM_CHANGE, PAN)


# TODO USE VELOCITY

# TODO TEMP
random.seed(SP.RANDOM_SEED)

dynam_axis = 0
pitch_axis = 1
time_axis = 2
length_axis = 3
pan_axis = 4
vel_axis = -1  # velocity data sits at the end


class PolyInterpreter(threading.Thread):
    """ Uses every boid as a sound source """

    def __init__(self, id_, midiout, swarm_data):
        """
        Make a new interpreter
        """
        super(PolyInterpreter, self).__init__()
        self.id = id_
        self.midiout = midiout
        self.swarm, self.channel = swarm_data
        self.instrument = Instruments.insts["HARP"]  # default instrument

        # make sure we're targeting the right channel with our MIDI messages
        self.control_change = CONTROL_CHANGE | self.channel
        self.note_on = NOTE_ON | self.channel
        self.note_off = NOTE_OFF | self.channel
        self.program_change = PROGRAM_CHANGE | self.channel

        self.time_elapsed = 0.0
        self.EVENT_START, self.EVENT_OFF = 1, 0

        # recording stuff
        self.recording = False
        self.send_midi = self.midi_message
        self.log = list()

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
        self.artic_min = IP.ARTIC_MIN
        self.artic_range = IP.ARTIC_RANGE
        self.probability = IP.PROBABILITY
        self.do_note_offs = 1
        self.scale = None
        self.notes = None
        self.range = 0
        self.set_scale(Scales.chrom)
        self.beat = None
        self.rhythms = None
        self.snap_to_beat = False
        self.interpret_time = self.interpret_time_free
        self.activate_instrument()

        self.done = False
        # self.start()

    def setup_interp(self, json_file):
        """
        Allows parameters to be set from JSON format
        :param json_file:
        :return:
        """
        data = json.load(open(json_file))

        for d in data.items():
            if d[0] == 'instrument':
                self.set_instrument(d[1])
            elif d[0] == 'pitch_min':
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
            elif d[0] == 'artic_min':
                self.artic_min = d[1]
            elif d[0] == 'artic_range':
                self.artic_range = d[1]
            else:
                print("Unexpected parameter: {}".format(d[0]))

        self.refresh()

    def refresh(self):
        """ refresh for when params have been changed """
        self.set_scale(self.scale)
        self.activate_instrument()

    def set_recording(self, new_rec):
        """ start or stop recording outgoing midi messages """
        # If we're recording and being told to stop...
        if not new_rec and self.recording:
            # Stop recording and write log to file
            print("I{}: Stopped recording.".format(self.id))
            self.recording = False
            self.send_midi = self.midi_message
            self.write_log_to_file()

        # If we're not recording and being told to start...
        elif new_rec and not self.recording:
            # Start recording
            print("I{}: Started recording....".format(self.id))
            self.recording = True
            self.send_midi = self.midi_message_log
            # make sure program change commands are sent again
            self.refresh()

        # If we're being nagged to do something we're already doing...
        else:
            pass  # wasted call

    def write_log_to_file(self):
        """ Write self.log to a pretty CSV """
        # should be a distinguishing-enough filename
        # any recording shorter than a second isn't worth keeping anyway
        filename = datetime.now().strftime("./recordings/%Y-%m-%d %H-%M-%S {}.csv".format(self.id))
        # Convert the log from [[Number]] to [[String]]
        s_log = [list(map(lambda x: str(x), xs)) for xs in self.log]

        # Flush the log :)
        self.log = list()

        # Write to the file
        with open(filename, 'w') as csvfile:
            writer = csv.writer(csvfile, lineterminator='\n')
            for row in s_log:
                writer.writerow(row)

        print("I{}: Written log to {}".format(self.id, filename))

    def midi_message(self, message, duration=None):
        """
        All MIDI messages go through here to be executed
        NOTE: duration is here for polymorphism only and is not used here
        """
        self.midiout.send_message(message)

    def midi_message_log(self, message, duration=None):
        """
        All MIDI messages that go through here get executed and written to a log
        NOTE: duration is for log only and does not affect audio output
        """
        self.midi_message(message, duration)
        if duration:
            message.append(duration)
        message.append(self.time_elapsed)
        self.log.append(message)

    def play_note(self, pitch, vol, duration=None):
        """
        Play a note
        :param pitch: midi pitch number
        :param vol: 0-127 volume
        :param duration: time until midi event ends (optional)
        """
        if random.random() < self.probability:
            self.send_midi([self.note_on, pitch, vol], duration=duration)

    def stop_note(self, pitch):
        """ stop a note playing """
        if self.do_note_offs:
            self.send_midi([self.note_on, pitch, 0], duration=0.0001)  # FIXME spoofing note_off with note_on

    def pan_note(self, val):
        """ Send a pan control message """
        self.send_midi([self.control_change, PAN, val & 127])

    def activate_instrument(self):
        # (drums are on channel 9)
        if self.channel != 9:
            # bank and program change
            bank, program = self.instrument
            self.send_midi([self.control_change, BANK_SELECT_MSB, bank & 0x7F])
            self.send_midi([self.program_change, program & 0x7F])

    def set_instrument(self, inst):
        try:
            self.instrument = Instruments.insts[inst.upper()]
            self.activate_instrument()
        except KeyError:
            print("{} not found. Please check spelling or consult Instruments.py for a full list".format(inst))

    def set_scale(self, scale):
        """
        Set the musical scale for the interpreter
        Assumes lowest pitch is the tonic
        :param scale: a scale from 'Scales.py' (in the form of a list of intervals)
        """
        self.scale = scale
        self.notes = Scales.gen_range(self.scale, lowest=self.pitch_min, note_range=self.pitch_range)
        self.range = len(self.notes)

    def set_tempo(self, beats_per_min):
        """
        Set the length in seconds of a single beat
        Also turns on beat snapping
        :param beats_per_min:
        :return:
        """
        self.beat = 60 / beats_per_min
        # self.rhythms = list(reversed([4, 3, 3, 2, 2, 3/2, 1, 1, 1, 1/2, 1/2, 1/2, 1/4]))  # TODO tinker with
        # self.rhythms = [2, 1, 1/2]
        self.rhythms = [1/4, 1/2, 1, 3/2, 2, 3, 4]
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

    def interpret_articulation(self, prop):
        return PolyInterpreter.lin_interp(prop, self.artic_min, self.artic_range)

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
        # TODO use velocity too
        # TODO this line has a big effect on the sound depending on the instrument:
        data[length_axis] = data[time_axis] * self.interpret_articulation(pos[length_axis])
        data[pan_axis] = self.interpret_pan(pos[pan_axis])
        return data

    def backwards_interpret(self, message, time):
        """
        Convert a midi input message to boid-space
        :param message: e.g. [144,47,120] (i.e. note on, B3, loud)
        :param time: in seconds, since last midi-in message
        """
        # TODO other sound dimensions are ignored/left average as midi input only has so much info

        # proportion along the axes (default middle)
        pitch_space = 0.5
        dynam_space = 0.5
        time_space = 0.5
        length_space = 0.5
        pan_space = 0.5

        pi_min, pi_ran = self.pitch_min, self.pitch_range
        d_min, d_ran = self.dynam_min, self.dynam_range
        t_min, t_ran = self.time_min, self.time_range  # TODO note that these are not used when beat is on
        # TODO length
        pa_min, pa_max = self.pan_min, self.pan_range

        # TODO catch more types of message
        # note on messages
        if 144 <= message[0] < 160:

            # DEBUG: PLAY THE INCOMING MESSAGE (on a different channel)
            # n.b. this has an alarmingly long delay despite the attractors appearing almost immediately
            # self.midiout.send_message([self.note_on | 1, message[1], message[2]])

            # TODO should account for the scale and take note of "wrong" notes
            if message[1] in range(pi_min, pi_min+pi_ran+1):
                pitch_space = (message[1]-pi_min)/pi_ran
            else:
                print("need something smarter for pitch: {0}".format(message[1]))

            dval = max(min(d_min+d_ran+1, message[2]), d_min)
            dynam_space = (dval - d_min) / d_ran

            if t_min <= time <= t_min+t_ran:
                time_space = (time-t_min)/t_ran
            else:
                print("need something smarter for time: {0}".format(time))

        self.swarm.place_attractor([dynam_space, pitch_space, time_space, length_space, pan_space])

    def setup_priority_queue(self, boid_heap, time_elapsed):
        """ Initialise a queue with the sound agents we will use """
        for boid in self.swarm.boids:
            # TODO the next few lines are copied in parse_priority_queue. fix if bothered
            next_data = self.interpret(boid.get_loc_ratios())
            if boid.feeding or not SP.FEEDING:
                self.pan_note(next_data[pan_axis])
                self.play_note(next_data[pitch_axis], next_data[dynam_axis], duration=next_data[length_axis])
            heappush(boid_heap, (time_elapsed + next_data[length_axis], (self.EVENT_OFF, next_data, boid)))
            heappush(boid_heap, (time_elapsed + next_data[time_axis], (self.EVENT_START, next_data, boid)))

    def parse_priority_queue(self, boid_heap, time_elapsed):
        """ Parse the data from the head of the queue """
        tag, data, boid = heappop(boid_heap)[1]

        if tag == self.EVENT_OFF:
            # stop note
            self.stop_note(data[pitch_axis])
        elif tag == self.EVENT_START:
            # interpret next data
            next_data = self.interpret(boid.get_loc_ratios())
            if boid.feeding or not SP.FEEDING:
                self.pan_note(data[pan_axis])
                self.play_note(next_data[pitch_axis], next_data[dynam_axis], duration=data[length_axis])
            # schedule next events
            heappush(boid_heap, (time_elapsed + next_data[length_axis], (self.EVENT_OFF, next_data, boid)))
            heappush(boid_heap, (time_elapsed + next_data[time_axis], (self.EVENT_START, next_data, boid)))
        else:
            print("Unexpected event type:", str(tag))

    def loop(self):
        """
        The main segement of the run method
        :return:
        """
        # set up priority queue of all the boids to be interpreted
        # time_elapsed = 0.0
        time_step = 0.05
        boid_heap = []

        self.setup_priority_queue(boid_heap, self.time_elapsed)

        # TODO add all notes to a list to ensure concurrency (as much as poss)
        while not self.done:

            time_this_loop = timenow()

            while boid_heap[0][0] <= self.time_elapsed:
                self.parse_priority_queue(boid_heap, self.time_elapsed)

            time_this_loop = timenow() - time_this_loop
            to_sleep = max(0, time_step - time_this_loop)
            if to_sleep == 0:
                print("OOPS: missed a beat (must be really lagging)")

            sleep(to_sleep)
            self.time_elapsed += time_step

    def run(self):
        # any necessary setup
        self.loop()
        # finish by stopping all the notes that may still be on
        self.send_midi([self.control_change, ALL_SOUND_OFF, 0])


class MonoInterpreter(PolyInterpreter):
    """ Uses the centre of gravity of the swarm, thus only playing one note at a time """

    def __init__(self, id_, midiout, swarm_data):
        super().__init__(id_, midiout, swarm_data)

    def setup_priority_queue(self, boid_heap, time_elapsed):
        """ Initialise a queue with the sound agents we will use """
        com = self.swarm.get_COM()
        data = self.interpret(com.get_loc_ratios())
        # TODO there's an odd delay at the start
        self.pan_note(data[pan_axis])
        self.play_note(data[pitch_axis], data[dynam_axis], duration=data[length_axis])
        # self.send_midi([self.note_on, data[pitch_axis], data[dynam_axis]])
        heappush(boid_heap, (time_elapsed + data[length_axis], (self.EVENT_OFF, data, com)))
        heappush(boid_heap, (time_elapsed + data[time_axis], (self.EVENT_START, data, com)))

    def parse_priority_queue(self, boid_heap, time_elapsed):
        """ Parse the data from the head of the queue """
        tag, data, com = heappop(boid_heap)[1]

        if tag == self.EVENT_OFF:
            # stop note
            self.stop_note(data[pitch_axis])
            pass
        elif tag == self.EVENT_START:
            # interpret next data
            next_data = self.interpret(com.get_loc_ratios())
            self.pan_note(data[pan_axis])
            self.play_note(next_data[pitch_axis], next_data[dynam_axis], duration=data[length_axis])
            # schedule next events
            heappush(boid_heap, (time_elapsed + next_data[length_axis], (self.EVENT_OFF, next_data, com)))
            heappush(boid_heap, (time_elapsed + next_data[time_axis], (self.EVENT_START, next_data, com)))
            pass
        else:
            print("Unexpected event type:", str(tag))
            pass


class RandomNotes(PolyInterpreter):
    """
    Literally just random stuff (ignoring swarm), for showing that the others are better (hopefully)
    (Annoyingly this actually sounds basically exactly the same............)
    """

    def __init__(self, id_, midiout, swarm_data):
        """ we inherit poly for convenience but don't need most of its functionality """
        super().__init__(id_, midiout, swarm_data)

    def loop(self):
        """ Play any old thing within the MIDI range """
        # TODO make something even more random to make me look better
        time_step = 0.1
        priority_queue = []
        chance = 0.5  # chance to play a note at any given time_step

        while not self.done:

            time_this_loop = timenow()

            # random chance to add a new event
            if random.random() < chance:
                note = random.randrange(0, 127)
                length = random.random() * 2
                volume = random.randrange(0, 127)
                print(note)
                self.send_midi([self.note_on, note, volume], duration=length)
                heappush(priority_queue, (self.time_elapsed + length, (note, length)))

            while priority_queue and priority_queue[0][0] <= self.time_elapsed:
                note, length = heappop(priority_queue)[1]
                self.send_midi([self.note_off, note], duration=length)

            time_this_loop = timenow() - time_this_loop
            to_sleep = max(0, time_step - time_this_loop)
            if to_sleep == 0:
                print("OOPS: missed a beat (must be really lagging)")

            sleep(to_sleep)
            self.time_elapsed += time_step
