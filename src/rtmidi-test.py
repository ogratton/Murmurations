import time
import rtmidi
from rtmidi import midiconstants as mc

note_list = [[63,65,0.55],
[63,65,0.55],
[29,74,0.501493444472511],
[59,71,0.4502455445257962],
[87,63,0.47265280701774653],
[101, 53, 0.521605475172954],
[99,50,0.5386637762914612],
[80,51,0.5285860582407333],
[49,67,0.4815164584222914],
[32,88,0.46852675240720953],
[36,93,0.5155380364757502],
[56,79,0.6186558603776737],
[73,50,0.7170259355792713],
[65,27,0.6183412308768639],
[59,50,0.4479193486378792],
[66,71,0.4131068443163868],
[78,84,0.4631219773024071],
[88,89,0.5183780103258905],
[83,79,0.5690245069499891],
[57,60,0.5862904648557028],
[38,58,0.5745962375815921],
[38,67,0.6220713883734839],
[63,72,0.6482372939115779],
[83,59,0.6644832304997248],
[77,40,0.49177541960741594],
[64,42,0.3814038162271516],
[57,54,0.336129741019703],
[53,66,0.3166602993241719],
[51,76,0.3501565544426007],
[51,86,0.41341652363898335],
[49,94,0.5049887477481234],
[53,93,0.6285533071900063],
[62,84,0.7640179525723299],
[68,71,0.8752976300760346]]

midiout = rtmidi.MidiOut()

for port_name in midiout.get_ports():
    print(port_name)

available_ports = midiout.get_ports()

if available_ports:
    midiout.open_port(0)
else:
    midiout.open_virtual_port("My virtual output")


def play_fifths(data):
    note_on = [mc.NOTE_ON, data[1], data[0]] # channel 1, middle C, velocity 112
    note2_on = [mc.NOTE_ON, data[1]+7, data[0]] # channel 1, middle C, velocity 112
    note_off = [mc.NOTE_OFF, data[1], 0]
    note2_off = [mc.NOTE_OFF, data[1]+7, data[0]]
    midiout.send_message([mc.PROGRAM_CHANGE, 65])
    midiout.send_message([mc.CONTROLLER_CHANGE, mc.MODULATION_WHEEL, 15])
    midiout.send_message([mc.CONTROLLER_CHANGE, mc.SUSTAIN, 65])
    midiout.send_message(note_on)
    midiout.send_message(note2_on)
    time.sleep(data[2])
    midiout.send_message(note_off)
    midiout.send_message(note2_off)

for data in note_list:
    play_fifths(data)

del midiout
