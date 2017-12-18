import threading

# temporary imports while it's a dummy
from time import sleep, time as timenow
import random

# TODO for now this outputs dummy data


class InStream(threading.Thread):
    """
    Listen to midi-in and publish the events
    """
    def __init__(self, interpreters):
        super(InStream, self).__init__()
        self.interpreters = interpreters
        self.done = False
        self.start()

    def run(self):
        # time since last event
        last_event_time = timenow()
        while not self.done:
            # poll for message TODO get real midi data
            message = [144, random.randint(0, 127), random.randint(0, 127)]
            print(message)
            # if we got anything...
            if message:
                # TODO calculate time somehow
                # if message[0] in range(128, 144):
                #     print("note off")
                # if message[0] in range(144, 160):
                #     print("note on")
                #     time_since_last = timenow() - last_event_time
                #     last_event_time = timenow()

                # publish the message to every interpreter
                for interp in self.interpreters:
                    interp.backwards_interpret(message)
                sleep(random.random())  # TODO only for dummy
