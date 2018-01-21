#!/usr/bin/env python
from MidiFile import *
from rtmidi.midiconstants import (CONTROL_CHANGE, NOTE_ON, NOTE_OFF, PROGRAM_CHANGE)
import csv

# GUI stuff
from PyQt5.QtWidgets import (QMainWindow, QTextEdit,
                             QAction, QFileDialog, QApplication)
from PyQt5.QtGui import QIcon
import sys

"""
Used for converting real-time MIDI performances to re-playable .mid files.
n.b.: writes to only one track.

Expected format of CSV:

The program outputs the logs automatically in the correct format, but should
you wish to use this outside of the project, this is how to ape it:

All messages are in the order one would expect of a normal MIDI message, e.g.:
    192, 90
is a program change to instrument 90 on channel 0.
The float on the end is the _absolute_ time at which this is to be sent.

In the special case of note_ons (144-159), the duration of the note is appended
to the end of the message as well. This makes the note_off handling trivial.
"""

# TODO WIP converting to multi-track


class MidiMaker:
    """ Takes a list of CSV logs and converts them to a single MIDI file """

    def __init__(self, logs_paths):
        self.time_offset = self.calculate_offset(logs_paths)

        self.myMIDI = MIDIFile(numTracks=len(logs_paths), adjust_origin=True)
        self.currentTrack = 0

        for log in logs_paths:
            self.add_track(log)

    @staticmethod
    def calculate_offset(log_paths):
        """ Find the earliest timestamp in all the logs and treat that as 0 """
        lowest_timestamp = float('inf')
        for log in log_paths:
            # read the first line of the file
            with open(log) as file:
                reader = csv.reader(file)
                first_line = reader.__next__()
                time = float(first_line[-1])
                if time < lowest_timestamp:
                    lowest_timestamp = time
        return lowest_timestamp

    def apply_offset(self, time):
        """ Apply the time offset """
        return time - self.time_offset

    def add_track(self, filepath):
        """ Read in a CSV log and write it to the correct track """
        time, tempo = 0, 60  # tempo 60 means 1 beat = 1 sec
        self.myMIDI.addTempo(self.currentTrack, time, tempo)

        # read log
        with open(filepath) as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                command = int(row[0])
                channel = command % 16
                fields = row[1:]
                time = self.apply_offset(float(fields[-1]))

                # CONTROL_CHANGE
                if 0 <= (command - CONTROL_CHANGE) < 16:
                    control_type, value = int(fields[0]), int(fields[1])
                    self.myMIDI.addControllerEvent(self.currentTrack, channel, time, control_type, value)
                # PROGRAM_CHANGE
                elif 0 <= (command - PROGRAM_CHANGE) < 16:
                    prog = int(fields[0])
                    self.myMIDI.addProgramChange(self.currentTrack, channel, time, prog)
                # NOTE_ON
                elif 0 <= (command - NOTE_ON) < 16:
                    pitch, volume = int(fields[0]), int(fields[1])
                    duration = float(fields[2])
                    self.myMIDI.addNote(self.currentTrack, channel, pitch, time, duration, volume)
                # NOTE_OFF
                elif 0 <= (command - NOTE_OFF) < 16:
                    # this is actually handled by the note_on having duration
                    # though I have a suspicion it makes them last to long...
                    # FIXME also not actually using them anymore
                    pass
                else:
                    # TODO catch other potenial MIDI messages
                    print("WARNING: Missed a message: {}".format(row))

        self.currentTrack += 1
        pass

    def write_midi(self, name):
        """ Write the final file """
        with open(name, "wb") as output_file:
            self.myMIDI.writeFile(output_file)


class Example(QMainWindow):
    def __init__(self):
        super().__init__()

        paths = self.show_dialog()
        if len(paths[0]):
            # take the first file's name for inspiration
            fname = paths[0][0][:-3] + "mid"
            MidiMaker(paths[0]).write_midi(fname)

    def show_dialog(self):
        fltr = "CSV (*.csv)"

        return QFileDialog.getOpenFileNames(self, "wow", filter=fltr)

if __name__ == "__main__":

    # TODO make a nice way to do this quickly (or automatically after recording)
    # dir = "./recordings/"
    # tag = "2018-01-21 19-43-23"
    # mm = MidiMaker([dir+tag+"0.csv", dir+tag+"1.csv"])
    # mm.write_midi(dir+"lovely.midi")

    app = QApplication(sys.argv)
    ex = Example()
    sys.exit()
