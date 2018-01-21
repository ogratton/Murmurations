#!/usr/bin/env python
from MidiFile import *
from rtmidi.midiconstants import (CONTROL_CHANGE, NOTE_ON, NOTE_OFF, PROGRAM_CHANGE)
import csv
import sys
import argparse

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

def offset(time_offset, time):
    """ Apply (or calculate) offset. A bit dumb """
    if time_offset is None:
        return time, 0.0
    else:
        return time_offset, time - time_offset

def write_from_log(csvfilename, midifilename):
    """ Convert a log of sent MIDI messages from real-time performance to a MIDI file """

    # One track, defaults to format 1 (tempo track is created automatically)
    myMIDI = MIDIFile(1, adjust_origin=True)
    track, time, tempo = 0, 0, 60  # tempo 60 means 1 beat = 1 sec
    myMIDI.addTempo(track, time, tempo)

    # CSVs use absolute time, and we need to shift it back to start at 0s
    time_offset = None

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
                time_offset, time = offset(time_offset, float(fields[2]))
                myMIDI.addControllerEvent(track, channel, time, control_type, value)
            # PROGRAM_CHANGE
            elif 0 <= (command - PROGRAM_CHANGE) < 16:
                prog = int(fields[0])
                time_offset, time = offset(time_offset, float(fields[1]))
                myMIDI.addProgramChange(track, channel, time, prog)
            # NOTE_ON
            elif 0 <= (command - NOTE_ON) < 16:
                pitch, volume = int(fields[0]), int(fields[1])
                duration = float(fields[3])
                time_offset, time = offset(time_offset, float(fields[2]))
                # TODO check:
                myMIDI.addNote(track, channel, pitch, time, duration, volume)
            # NOTE_OFF
            elif 0 <= (command - NOTE_OFF) < 16:
                # this is actually handled by the note_on having duration
                # though I have a suspicion it makes them last to long...
                pass
            else:
                # TODO catch other potenial MIDI messages
                print("Missed a message: {}".format(row))

    # write to file
    with open(midifilename, "wb") as output_file:
        myMIDI.writeFile(output_file)


def main(args):
    """ Bit overkill seeing as I only have 2 args but oh well """
    ap = argparse.ArgumentParser(description="Convert CSV log to MIDI file")
    aadd = ap.add_argument
    aadd('-l', '--log', type=str, help="Input log file name (w/ extension)")
    aadd('-o', '--output', type=str, help="Filename of output (w/ extension)")

    args = ap.parse_args(args if args is not None else sys.argv[1:])

    log = args.log
    def_name = ''.join(log.split('.')[:-1])
    out = def_name if args.output is None else args.output

    if log is not None:
        write_from_log(log, out)
    else:
        print("Please provide an input file with -l")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]) or 0)
