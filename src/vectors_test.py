from vectors import Vector3, Vector4, Vector5, Vector6
from pygame.math import Vector3 as pgVect3
from numpy import r_
from numpy.linalg import norm

# i = Vector4([1, 2, 3, 4])
# j = Vector4([5, 4, 3, 2])
# k = Vector5([3, 4, 5, 6, 7])
# m = Vector6([5, 7, 4, 2, 6, 8])
# l = Vector4()
#
# print(i + j)
# print(i - j)
# print(i * j)
# print(i / j)
# print(i.get(0))
# print(j.get(3))
# print(i.distance_to(j))
# print(i.length())
#
# print(i.normalize())
# print(l)
# print(i + 5)
# print(j / 2)
# print(j * 2.5)
#
# print(i.normalize() + j * 2.5)
#
# print(m)
#
# print(Vector6.n)

a = Vector3([1, 2, 3])
b = Vector3([4, 5, 6])
i = pgVect3(1, 2, 3)
j = pgVect3(4, 5, 6)
x = r_[1, 2, 3]
y = r_[4, 5, 6]

print(a*5)
print(i*5)
print(x*5)

print(a+5)
#print(i+5)  # lol no
print(x+5)

print(a.normalize())
print(i.normalize())
print(x/norm(x))


c = Vector5([4,6,6,7,6])
d = Vector5([2,7,4,7,4])

g = r_[4,6,6,7,6]
h = r_[2,7,4,7,4]

print(c*5)
print(g*5)

print(d.normalize())
print(h/norm(h))

print(h[0])