from obs import Observer
import threading
import time
from random import randint


"""
Interpret the centre of mass of swarms as parameters for music
Each c.o.m represents one musical line
Needs to "listen" to a SwarmRender.Renderer to get c.o.m
"""

exitFlag = False

# TODO i need to know which swarm each COM is from, and the v_min of each of these so they can be scaled


class Receiver(Observer):
    """
    Receieves the centre of mass data from (each?) swarm
    """
    def update(self, *args, **kwargs):
        print(args)

    def convert(self):
        """
        Convert the centre of mass data into a midi note with pitch and dynamic
        :return:
        """
        print("TODO")


class Listener(threading.Thread):
    def __init__(self, swarm_index, name, renderer):
        threading.Thread.__init__(self)
        self.swarm_index = swarm_index
        self.name = name
        self.renderer = renderer
        self.com = []

    def run(self):
        print("Starting " + self.name)
        while True:
            # self.com = self.renderer.swarms[self.swarm_index].get_COM() # TODO this is the real line
            self.com = self.renderer.get_COM()
            print(self.com)

            if self.com[1] < 5:
                self.exit()  # ??

            time.sleep(self.com[2])


class DummyRenderer(object):
    """
    Will generate fake COM data for thread testing
    """
    def __init__(self):
        self.com = [0, 0, 0]

    def update(self):
        self.com = list(map(lambda x: randint(1, 9), self.com))

    def get_COM(self):
        return self.com


def dummy_main():
    renderer = DummyRenderer()
    listener = Listener(1, "listener", renderer)
    listener.start()
    print("started?")
    while True:
        renderer.update()
        exitFlag = True

dummy_main()
