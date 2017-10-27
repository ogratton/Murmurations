import time
import rtmidi
from rtmidi import midiconstants as c


class Player:
    """
    Play midi notes
    """
    def __init__(self, port, instrument):
        """
        Initialise the midiout channel
        """
        self.midiout = rtmidi.MidiOut()
        self.available_ports = self.midiout.get_ports()
        print(self.available_ports)
        self.instrument = instrument
        # self.midiout.send_message([c.PROGRAM_CHANGE, instrument])

        self.midiout.open_port(port)

    # # TODO god knows if this works
    # def __del__(self):
    #     del self.midiout

    def play_note(self, data):
        """
        Actually play a note through the midi channel
        :param data: list of [dynamic, pitch, length]
        """
        self.midiout.send_message([c.PROGRAM_CHANGE, self.instrument])
        note_on = [c.NOTE_ON, data[1], data[0]]  # middle C, velocity 112
        note_off = [c.NOTE_OFF, data[1], 0]
        self.midiout.send_message(note_on)
        time.sleep(data[2])
        self.midiout.send_message(note_off)