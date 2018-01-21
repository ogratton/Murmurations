import mido
from mido import MidiFile
from time import sleep

port = mido.open_output('LoopBe Internal MIDI 2')

mid = MidiFile('2018-01-21 23-03-00 0.mid')

for msg in mid.play():
    port.send(msg)

