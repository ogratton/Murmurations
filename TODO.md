# TODO

Move points to logbook when done

## Swarm

* Make n-dimensional (just make my own vector class)
* (?) Add hierarchical clustering to determing centre of mass of largest part of a swarm
* Tweak values in rules
* Add predators


## Music

* Add sustain & modulation and stuff
	* 'let ring'
* Quantize time axis, but maybe with some gaussian noise for human-like sloppiness
* Custom interpretation types for different instruments (restrict pitch to its range)
* Snap-to-scale pitch
* Dynamics need to change less regularly (but still have the ability for subitos)
* Allow for silence/rests (this should come with the note duration dimension)

## Graphics

* **CHANGE FROM PYGAME TO PYGLET**
* Change boids from lines to spheres/circles
* Manual rotation about the focal point with mouse/arrow keys


## Admin

* Fill in README
* Write some unit tests (see Observable folder on home PC)


## Misc

* Tidy up SwarmMain.py cos it is horrible
* Look at Numba & CUDA for GPU use
	* https://developer.nvidia.com/how-to-cuda-python
	* https://github.com/numba/numba/blob/master/examples/objects.py