#!/usr/bin/env python
from MidiFile import *
from rtmidi.midiconstants import (CONTROL_CHANGE, NOTE_ON, NOTE_OFF, PROGRAM_CHANGE)
import csv

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


def write_from_log(csvfilename, midifilename):
    """ Convert a log of sent MIDI messages from real-time performance to a MIDI file """

    # One track, defaults to format 1 (tempo track is created automatically)
    myMIDI = MIDIFile(1, adjust_origin=True)
    track, time, tempo = 0, 0, 60  # tempo 60 means 1 beat = 1 sec
    myMIDI.addTempo(track, time, tempo)

    # read log
    with open(csvfilename) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:

            command = int(row[0])
            fields = row[1:]

            channel = command % 16
            # CONTROL_CHANGE
            if 0 <= (command - CONTROL_CHANGE) < 16:
                control_type, value = int(fields[0]), int(fields[1])
                time = float(fields[2])
                myMIDI.addControllerEvent(track, channel, time, control_type, value)
            # PROGRAM_CHANGE
            elif 0 <= (command - PROGRAM_CHANGE) < 16:
                prog, time = int(fields[0]), float(fields[1])
                myMIDI.addProgramChange(track, channel, time, prog)
            # NOTE_ON
            elif 0 <= (command - NOTE_ON) < 16:
                pitch, volume = int(fields[0]), int(fields[1])
                time, duration = float(fields[2]), float(fields[3])
                # TODO check:
                myMIDI.addNote(track, channel, pitch, time, duration, volume)
            # NOTE_OFF
            elif 0 <= (command - NOTE_OFF) < 16:
                # this is actually handled by the note_on having duration
                pass
            else:
                # TODO catch other potenial MIDI messages
                print("Missed a message: {}".format(row))

    # write to file
    with open(midifilename, "wb") as output_file:
        myMIDI.writeFile(output_file)

if __name__ == "__main__":
    write_from_log("test_record_2.csv", "test_record_2.mid")