import threading
from time import sleep
from rtmidi.midiconstants import (ALL_SOUND_OFF, CHANNEL_VOLUME,
                                  CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)
from parameters import IP


"""
Interpret the centre of mass of swarms as parameters for music
Each c.o.m represents one musical line
"""

# CONSTANTS
DYNAM_RANGE = IP.DYNAM_MAX - IP.DYNAM_MIN


class NaiveSequencer(threading.Thread):
    """MIDI output thread."""

    def __init__(self, name, midiout, swarm_data, volume=127):
        super(NaiveSequencer, self).__init__()
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

        while not self.done:
            data = interpret(self.swarm.cube.edge_length, self.swarm.get_COM().get_location())
            self.midiout.send_message([NOTE_ON | self.channel, data[1], data[0] & 127])
            sleep(max(IP.TIME_MIN, data[2]))
            self.midiout.send_message([NOTE_ON | self.channel, data[1], 0])

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
    return int((value / max_v) * IP.PITCH_RANGE + IP.PITCH_MIN)


def interpret_time(max_v, value):
    return (value/max_v) * IP.TIME_RANGE + IP.TIME_MIN


def interpret_dynamic(max_v, value):
    return int((value/max_v) * DYNAM_RANGE + IP.DYNAM_MIN)
