# TODO

Move points to logbook when done

## Swarm

* Smaller paths for attractors to encourage repetition
* Stigmery between swarms: Think about how swarms can interact with one another (add their position as attractor)
* Attractors as food sources (renewable for path-mode but non- for user input mode)
	* Though that then makes stigmergy between swarms a bit odd...
* Do away with cubes and have the bounds determined by how the flock moves
* Make separation spongier
* Add predators
	* Patrolling predators can reduce the probability of a swarm visiting an area of music space without making it impossible
	* e.g. a predator patrolling the lower half of a box will make it less likely that the swarm get down there
	* Think of a way to implement them without having to check every boid and every boid check every predator (laggy af)
* Treat attractors as high gravity points and have boids orbit them and speed up as they get closer
	* Equates to adding gravity rule(?), which then means the boids and attractors must be assigned masses
* Likewise have it so that the boids slow down as they approach the attractor
* Dynamic number of boids (may play havoc with existing code)
* More complex swarm behaviour: (see Reynolds87 and https://en.wikipedia.org/wiki/Flocking_(behavior)#Flocking_rules)
	* Roll leads to drop in height
	* Fear propogation
	* Fixed topolgical distance (i.e. look for k nearest neighbours instead of in a radius)


## Music

* Extra dimensions can determine scale/key etc
* Only play when near (i.e. eating) an attractor
* Add sustain & modulation and stuff
	* 'let ring'
	* if using the Sonuus G2M, this could potentially be done via a breakout cable
* Make instrument-specific presets (e.g. piano, double bass)
* Dynamics need to change less regularly (but still have the ability for _subito_s)
* Allow for silence/rests (this _should_ come with the note duration dimension)
* Attractor input from live input
    * Musician
	* VR/Wii conductor
	* Or Dancer...? (kinect)
* Work out best configurations for jazz, classical etc.
* A sort of loop pedal to capture phrase/melody ideas
* Have a look at this interesting rhythm idea https://www.youtube.com/watch?v=2UphAzryVpY

## Graphics

* Fix rotation for boids (match velocity)
* Add centre of gravity model?
* Change the way the camera movement works
* Add MC-Edit-style GUI
    * add swarms (by dragging and dropping?)
	* tweak settings on the fly
* OR do visuals in unity3d and send data over server


## Admin

* Fill in README
* Write some unit tests (see Observable folder on home PC)
* Start report paint-by-numbers style (top-down)


## Misc

* Don't think the random seed thing is working for the swarm
* Make code even more modular if possible (I don't like how pyglet is tied into it)
* Look at Numba & CUDA for GPU use
	* https://developer.nvidia.com/how-to-cuda-python
	* https://github.com/numba/numba/blob/master/examples/objects.py
* If you can't speed up VectorN with CUDA etc., try writing it in C
	* http://intermediate-and-advanced-software-carpentry.readthedocs.io/en/latest/c++-wrapping.html
	* Maybe outdated: https://www.safaribooksonline.com/library/view/python-cookbook/0596001673/ch16s06.html
* Error catching now we have a config file
* To find good parameters, have an approval gauge like in political debates
  but it's just me pressing a button faster or slower depending how much I like
  what is playing as the system tweaks its own parameters
* Catch normalising zero vectors
