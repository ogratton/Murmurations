import mido
from mido import MidiFile
from time import sleep

# TODO make a nice player GUI
# and maybe have integrated playback too

port = mido.open_output('LoopBe Internal MIDI 2')

mid = MidiFile('2018-01-22 00-13-15 0.mid')

for msg in mid.play():
    port.send(msg)

