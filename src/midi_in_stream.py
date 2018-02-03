import threading

from rtmidi.midiutil import open_midiinput
from time import sleep, time as timenow
import random

# TODO for now this outputs dummy data


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
            self.midiin, self.port_name = open_midiinput(port)
            print("Listening for midi on port {}".format(port))
        except (EOFError, KeyboardInterrupt):
            print("WARNING: failed to open MIDI-in port {0}".format(port))

        self.done = False
        self.start()

    def run(self):
        while not self.done:
            msg = self.midiin.get_message()
            # TODO for now only listen to NOTE_ON
            if msg:
                message, deltatime = msg
                if 144 <= message[0] < 160:
                    self.wallclock += deltatime
                    # print("[%s] @%0.6f %r" % (self.port_name, self.wallclock, message))

                    # publish the message to every interpreter
                    for interp in self.interpreters:
                        interp.backwards_interpret(message, random.random())  # TODO time

            sleep(0.01)


# TODO remove
class DummyInStream(threading.Thread):
    """
    Sends made-up midi messages to the interpreters
    """
    def __init__(self, interpreters):
        super(DummyInStream, self).__init__()
        self.interpreters = interpreters
        self.done = False
        self.start()

    def run(self):
        # time since last event
        last_event_time = timenow()
        time_since_last = 0
        while not self.done:
            # poll for message TODO get real midi data
            message = [144, random.randint(0, 127), random.randint(0, 127)]
            # if we got anything...
            if message:
                # TODO calculate time somehow
                # TODO note that time_since_last will scupper chords :(
                # perhaps send the last value that wasn't tiny...?
                if 144 <= message[0] < 160:
                    time_since_last = timenow() - last_event_time
                    last_event_time = timenow()

                # publish the message to every interpreter
                for interp in self.interpreters:
                    interp.backwards_interpret(message, time_since_last)
                sleep(random.random())  # TODO only for dummy