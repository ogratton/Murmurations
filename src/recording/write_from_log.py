#!/usr/bin/env python
from MidiFile import *
from rtmidi.midiconstants import (CONTROL_CHANGE, NOTE_ON, NOTE_OFF, PROGRAM_CHANGE)
import csv


# One track, defaults to format 1 (tempo track is created automatically)
myMIDI = MIDIFile(1, adjust_origin=True)
track, time, tempo = 0, 0, 60  # tempo 60 means 1 beat = 1 sec
myMIDI.addTempo(track, time, tempo)

with open('test_record_1.csv') as csvfile:
    reader = csv.reader(csvfile)
    for row in reader:
##        # convert the first few elements
##        nums = list(map(lambda x: int(x), row[:-1]))
##        # time & duration always at the end of the line
##        time = float(row[-1])
##        command, fields = nums[0], nums[1:]
##        print("{}:\t{}\t{:1f}".format(command, fields, time))
        command = int(row[0])
        fields = row[1:]

        channel = command % 16
        # CONTROL CHANGES
        if 0 <= (command - CONTROL_CHANGE) < 16:
            # TODO (bank select, pan, all notes off etc.
            control_type, value = int(fields[0]), int(fields[1])
            time = float(fields[2])
            myMIDI.addControllerEvent(track, channel, time, control_type, value)
        # PROGRAM CHANGE
        elif 0 <= (command - PROGRAM_CHANGE) < 16:
            prog, time = int(fields[0]), float(fields[1])
            myMIDI.addProgramChange(track, channel, time, prog)
        # NOTE ON
        elif 0 <= (command - NOTE_ON) < 16:
            pitch, volume = int(fields[0]), int(fields[1])
            time, duration = float(fields[2]), float(fields[3])
            # TODO check:
            myMIDI.addNote(track, channel, pitch, time, duration, volume)
        # NOTE OFF
        elif 0 <= (command - NOTE_OFF) < 16:
            pass # think this is actually handled by the note_on having duration

with open("test_record_1.mid", "wb") as output_file:
    myMIDI.writeFile(output_file)
