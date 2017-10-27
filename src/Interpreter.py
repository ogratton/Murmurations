import Sound
import threading
import time


"""
Interpret the centre of mass of swarms as parameters for music
Each c.o.m represents one musical line
Needs to "listen" to a SwarmRender.Renderer to get c.o.m
"""

# CONSTANTS

pitch_range = 88    # 88 keys on a piano, so seems suitable
pitch_min = 21      # A0
time_range = 1      # range in time between events
time_min = 0.05     # min time between events
dynam_range = 127   # range of dynamics
dynam_min = 0       # min dynamic TODO this is just silence, so maybe higher


class Listener(threading.Thread):
    def __init__(self, swarm_index, name, swarm, player):
        threading.Thread.__init__(self)
        self.swarm_index = swarm_index
        self.name = name
        self.swarm = swarm
        self.player = player
        self.running = False

    def run(self):
        print("Starting " + self.name)
        self.running = True
        # TODO hard exit (this waits for current sleep to finish)
        while self.running:
            # Get the centre of mass of our swarm and interpret it
            data = interpret(self.swarm.cube.edge_length, self.swarm.get_COM().get_location())
            print(str(self.swarm_index) + ": " + str(data))
            self.player.play_note(data)
            time.sleep(data[2])
        print("Ending " + self.name)

    def stop(self):
        self.running = False


def interpret(max_v, data):
    """
    :param max_v: the maximum value each data can have
    :param data: list of positional data (x,y,z...)
    :return: the list with the functions applied to each dimension
    """
    # TODO hard-coded for 3D
    return [interpret_dynamic(max_v, data[0]), interpret_pitch(max_v, data[1]), interpret_time(max_v, data[2])]


def interpret_pitch(max_v, value):
    """
    Convert positional value into pitch for MIDI
    :param max_v: int, the maximum value <value> can be
    :param value: float, distance along the axis associated with pitch
    :return: int from 21-108 to stay within piano range
    """
    return int((value / max_v) * pitch_range + pitch_min)


def interpret_time(max_v, value):
    return (value/max_v) * time_range + time_min


def interpret_dynamic(max_v, value):
    return int((value/max_v) * dynam_range + dynam_min)