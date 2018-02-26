import threading

from rtmidi.midiutil import open_midiinput
from rtmidi import MidiIn
from time import sleep, time as timenow
import random

class InStream(threading.Thread):
    """
    Polls midi-in and publish the events
    Based on the midiin_callback code from python rt-midi examples
    """
    def __init__(self, interpreters, port):
        super(InStream, self).__init__()
        self.interpreters = interpreters
        self.port = port
        self.wallclock = timenow()

        try:
            self.midiin = MidiIn().open_port(port)
            print("Listening for midi on input port {}".format(port))
        except (EOFError, KeyboardInterrupt):
            print("WARNING: failed to open MIDI-in port {0}".format(port))

        self.done = False
        self.start()

    def run(self):
        while not self.done:
            msg = self.midiin.get_message()
            # TODO for now only listen to NOTE_ON & OFF
            if msg:
                message, delta_time = msg
                if 128 <= message[0] < 160:
                    self.wallclock += delta_time
                    # print("[%s] @%0.6f %r" % (self.port_name, self.wallclock, message))

                    # publish the message to every interpreter
                    for interp in self.interpreters:
                        interp.backwards_interpret(message, delta_time)

            sleep(0.01)
