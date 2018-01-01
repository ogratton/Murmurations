#!/bin/bash
cython Swarm.pyx -a
gcc -shared -pthread -fPIC -fwrapv -O2 -Wall -fno-strict-aliasing -ffast-math -I/usr/include/python3.5 -I/usr/local/lib/python3.5/dist-packages/numpy/core/include -o Swarm.so Swarm.c

