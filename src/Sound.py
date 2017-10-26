import time
import rtmidi


class Player():
    """
    Play midi notes
    """
    def __init__(self):
        """
        Initialise the midiout channel
        """
        # TODO very temporary
        self.midiout = rtmidi.MidiOut()
        self.available_ports = self.midiout.get_ports()

        if self.available_ports:
            self.midiout.open_port(0)
        else:
            self.midiout.open_virtual_port("My virtual output")

    def play_note(self, data):
        """
        Actually play a note through the midi channel
        :param data: list of [dynamic, pitch, length]
        :return:
        """
        note_on = [0x90, data[1], data[0]]  # channel 1, middle C, velocity 112
        note_off = [0x80, data[1], 0]
        self.midiout.send_message(note_on)
        time.sleep(data[2])
        self.midiout.send_message(note_off)
