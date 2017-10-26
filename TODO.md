# TODO

Move points to logbook when done

## Swarm

* Make n-dimensional (just make my own vector class)
* (?) Add hierarchical clustering to determing centre of mass of largest part of a swarm
* Tweak values in rules
* Add attractors
* Add predators


## Music

* Add "poller" to convert centre of mass of swarm to a single note
	* It should run on a separate thread and only request COM when it needs it 


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