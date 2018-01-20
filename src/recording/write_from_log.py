#!/usr/bin/env python
from midiutil import MIDIFile
import csv

# TODO not right yet

# One track, defaults to format 1 (tempo track is created automatically)
myMIDI = MIDIFile(1, adjust_origin=True)
track, time, tempo = 0, 0, 120
myMIDI.addTempo(track, time, tempo)

with open('log2.csv') as csvfile:
    reader = csv.reader(csvfile, quotechar='#')
    for row in reader:
        # convert the first few elements
        nums = list(map(lambda x: int(x), row[:-1]))
        # time is always at the end of the line
        time = float(row[-1])
        command, fields = nums[0], nums[1:]
        print("{}:\t{}\t{:1f}".format(command, fields, time))

        # TODO handle other midi messages (e.g. 176-191)
        channel = command % 16
        # PROGRAM CHANGE
        if 0 <= (command - 192) < 16:
            prog = fields[0]
            myMIDI.addProgramChange(track, channel, time, prog)
        # NOTE ON
        if 0 <= (command - 144) < 16:
            pitch, volume = fields
            # TODO check:
            # because we're sending note_ons as offs too, we can spoof duration
            duration = 10
            myMIDI.addNote(track, channel, pitch, time, duration, volume)

with open("song2.mid", "wb") as output_file:
    myMIDI.writeFile(output_file)
