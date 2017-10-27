# import time
# import rtmidi
# from rtmidi import midiconstants as c
#
#
# """ DEPRECATED """
#
# class Sequencer:
#     """
#     Play midi notes
#     """
#     def __init__(self, midiout, channel, instrument):
#         """
#         Initialise sequencer
#         """
#         self.midiout = midiout
#         self.channel = channel
#         self.instrument = instrument
#         # self.midiout.send_message([c.PROGRAM_CHANGE, instrument])
#
#
#     # # TODO god knows if this works
#     # def __del__(self):
#     #     del self.midiout
#
#     def play_note(self, data):
#         """
#         Actually play a note through the midi channel
#         :param data: list of [dynamic, pitch, length]
#         """
#         self.midiout.send_message([c.PROGRAM_CHANGE | self.channel, self.instrument & 127])
#         note_on = [c.NOTE_ON | self.channel, data[1], data[0]]  # middle C, velocity 112
#         note_off = [c.NOTE_OFF | self.channel, data[1], 0]
#         self.midiout.send_message(note_on)
#         time.sleep(data[2])
#         self.midiout.send_message(note_off)
