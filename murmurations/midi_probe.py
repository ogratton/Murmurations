import rtmidi

# prints all the available midi in & out ports on the system

print("OUT PORTS:")

midiout = rtmidi.MidiOut()
for i, port_name in enumerate(midiout.get_ports()):
    print("[" + str(i) + "]", port_name)

print("\n\n")

print("IN PORTS:")

midiin = rtmidi.MidiIn()
for i, port_name in enumerate(midiin.get_ports()):
    print("[" + str(i) + "]", port_name)
