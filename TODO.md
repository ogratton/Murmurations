# TODO

Move points to logbook when done

## Swarm

* Tweak values in rules
* Add predators
* Think how swarms can interact with one another


## Music

* Add sustain & modulation and stuff
	* 'let ring'
* Quantize time axis, but maybe with some gaussian noise for human-like sloppiness
* Custom interpretation types for different instruments (restrict pitch to its range)
* Snap-to-scale pitch
* Dynamics need to change less regularly (but still have the ability for subitos)
* Allow for silence/rests (this should come with the note duration dimension)

## Graphics

* Add centre of gravity model? (triangle?)
* Change the way the camera movement works
* Add rotation for boids (match velocity)
* Add GUI to add swarms and tweak settings on the fly


## Admin

* Fill in README
* Write some unit tests (see Observable folder on home PC)


## Misc

* Look at Numba & CUDA for GPU use
	* https://developer.nvidia.com/how-to-cuda-python
	* https://github.com/numba/numba/blob/master/examples/objects.py
* If you can't speed up VectorN with CUDA etc., try writing it in C
	* http://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/c++-wrapping.html
	* Maybe outdated: https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch16s06.html