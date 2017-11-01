from abc import ABCMeta
from typing import List
from math import sqrt
from operator import add, sub, truediv

"""
n-dimensional vector class

mimics the base functionality of pygame.math.Vector3
"""

# TODO NOTE THAT THIS IS REALLY LAGGY COMPARED TO PYGAME'S COS THEIR'S IS WRITTEN IN C
# If you're feeling brave/desperate you could try and write your own in c like they did
# https://github.com/pygame/pygame/blob/master/src/math.c
# https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch16s06.html
# http://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/c++-wrapping.html
# TODO docstrings


class VectorN(object):
    __metaclass__ = ABCMeta

    def __init__(self, data: List[float], cls):
        self.data = data
        self.dims = len(data)
        self.cls = cls

    def __repr__(self):
        return "vec: " + str(self.data)

    def __add__(self, other):
        return self.maths(add, other)

    def __sub__(self, other):
        return self.maths(sub, other)

    def __truediv__(self, other):
        # will probably never be used
        return self.maths(truediv, other)

    def __mul__(self, other):
        # different from others because we want dot product, not Hadamard
        if isinstance(other, VectorN):
            assert other.dims == self.dims
            return sum([a*b for a, b in zip(self.data, other.data)])
        else:
            return self.cls(list(map(lambda x: x*other, self.data)))

    def as_list(self):
        return self.data

    def get(self, index):
        assert index < self.dims
        return self.data[index]

    def maths(self, f, other):
        """
        :param f: operator function, e.g. add, sub...
        :param other: thing to be mathsed
        :return: result
        """
        if isinstance(other, VectorN):
            assert other.dims == self.dims
            return self.cls([f(a, b) for a, b in zip(self.data, other.data)])
        else:
            return self.cls(list(map(lambda x: f(x, other), self.data)))

    def normalize(self):
        """
        :return: a vector with the same direction but length 1
        """
        s = self.length()
        if s:
            return self.cls(list(map(lambda x: x / s, self.data)))
        else:
            return self.cls()

    def length(self):
        """
        :return: Euclidean length of the vector
        """
        return sqrt(sum(i*i for i in self.data))

    def distance_to(self, other):
        """
        :param other: another vector with the same dimensionality
        :return: Euclidean distance to other
        """
        assert other.dims == self.dims
        return sqrt(sum((i-j)**2 for i, j in zip(self.data, other.data)))


"""
PRE-MADE FOR YOUR CONVENIENCE:
"""


class Vector6(VectorN):

    n = 6

    def __init__(self, data=None):
        if data is None:
            data = [0]*self.n
        assert len(data) == self.n
        super().__init__(data, Vector6)


class Vector5(VectorN):

    n = 5

    def __init__(self, data=None):
        if data is None:
            data = [0]*self.n
        assert len(data) == self.n
        super().__init__(data, Vector5)


class Vector4(VectorN):

    n = 4

    def __init__(self, data=None):
        if data is None:
            data = [0]*self.n
        assert len(data) == self.n
        super().__init__(data, Vector4)


class Vector3(VectorN):

    n = 3

    def __init__(self, data=None):
        if data is None:
            data = [0]*self.n
        assert len(data) == self.n
        super().__init__(data, Vector3)
