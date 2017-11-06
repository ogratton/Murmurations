from abc import ABCMeta, abstractmethod
import threading
from rtmidi.midiconstants import (ALL_SOUND_OFF, CHANNEL_VOLUME,
                                  CONTROL_CHANGE, NOTE_ON, PROGRAM_CHANGE)
from parameters import IP


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