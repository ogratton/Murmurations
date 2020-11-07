import threading
from time import sleep, time as timenow

from rtmidi import MidiIn

from . import parameters


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
        except Exception:
            print("WARNING: failed to open MIDI-in port {0}".format(port))

        self.done = False
        self.run = self.run_bound if parameters.SP.ATTRACTOR_MODE == 1 else self.run_att
        # print(self.run.__name__)
        self.start()

    def run_att(self):
        """ For use with attractor mode 2, which is old and bad """
        # TODO experimental timings
        buffer_time = 0.05
        while not self.done:
            started = timenow()
            buffer = list()
            while (timenow() - started) < buffer_time:
                msg = self.midiin.get_message()
                if msg:
                    buffer.append(msg)
                sleep(0.002)

            chord_time = buffer_time
            if len(buffer) >= 1:
                if buffer[0]:
                    chord_time = buffer[0][1]
                for msg in buffer:
                    message, delta_time = msg
                    # TODO for now only listen to NOTE_ON & OFF
                    if 128 <= message[0] < 160:
                        self.wallclock += delta_time
                        # print("[%s] @%0.6f %r" % (self.port_name, self.wallclock, message))

                        # publish the message to every interpreter
                        for interp in self.interpreters:
                            interp.backwards_interpret(message, chord_time)

            sleep(0.01)  # TODO need this?

    def run_bound(self):
        """ For use with attractor mode 1, and is not yet done """
        # gather <event_time> seconds of notes and analyse them for:
        #   - pitch min & range
        #   - time min & range
        #   - dynam min & range
        #   - (if possible, the duration of notes, from note off messages)
        event_time = 0.5  # TODO maybe this should adapt to the pace of the music?
        buffer_time = 0.05

        while not self.done:
            started = timenow()
            p_min, d_min, t_min = [float("inf")] * 3
            p_max, d_max, t_max = [0] * 3
            event_notes = list()

            # a single event
            while timenow() - started < event_time:
                b_started = timenow()
                delta_t = -1

                # buffer, so chords count as simultaneous notes
                while timenow() - b_started < buffer_time:
                    msg = self.midiin.get_message()
                    if msg:
                        message, d_t = msg
                        if delta_t == -1:
                            delta_t = d_t
                        event_notes.append((message, delta_t))
                    sleep(0.002)

            num_note_ons = 0

            # analyse event_notes for all the fun stuff
            for (message, time) in event_notes:

                if 144 <= message[0] < 160:
                    note_on, pitch, dynam = message
                    p_min = min(p_min, pitch)
                    p_max = max(p_max, pitch)
                    d_min = min(d_min, dynam)
                    d_max = max(d_max, dynam)
                    t_min = min(t_min, time)
                    t_max = max(t_max, time)
                    num_note_ons += 1
                    # TODO duration
                elif 128 < message[0] < 144:
                    # until we do duration, we don't care
                    pass

            # if there's anything to report
            if num_note_ons:
                p_rng, d_rng, t_rng = (p_max - p_min), (d_max - d_min), (t_max - t_min)

                for interp in self.interpreters:
                    # print(p_min, p_rng, d_min, d_rng, t_min, t_rng)
                    interp.change_bounds(p_min, p_rng, d_min, d_rng, t_min, t_rng)
                    # pass

            sleep(0.5)
