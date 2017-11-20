# TODO

Move points to logbook when done

## Swarm

* Make separation spongier
* Random noise on values for each boid to create actual individuals
* Tweak values in rules/config.ini
* Add predators
* Think about how swarms can interact with one another (add their position as attractor)
* Define paths for attractors rather than randomly placing them
* Treat attractors as high gravity points and have boids orbit them and speed up as they get closer
	* Equates to adding gravity rule(?), which then means the boids and attractors must be assigned masses
* Likewise have it so that the boids slow down as they approach the attractor
* Dynamic number of boids (may play havoc with existing code)
* Multiple attractors to split the swarm? (Only desirable with ChordSeq)
	* will probably happen anyway with swarm stigmergy


## Music

* Account for computation time for beats (like DrumSeq)
* Add sustain & modulation and stuff
	* 'let ring'
	* if using the Sonuus G2M, this could potentially be done via a breakout cable
* Custom interpretation types for different instruments (restrict pitch to its range)
* Dynamics need to change less regularly (but still have the ability for subitos)
* Allow for silence/rests (this _should_ come with the note duration dimension)
* Attractor input from live input
    * Musician
	* VR/Wii conductor
	* Or Dancer...? (kinect)
* Output midi file too so I can open in musescore (or at least write to log file)?
* Use virtual ports (JACK or switch to UNIX) to play real MIDI instruments
* Work out best configurations for jazz, classical etc.
* A sort of loop pedal to capture phrase/melody ideas
* Have a look at this interesting rhythm idea https://www.youtube.com/watch?v=2UphAzryVpY

## Graphics

* Add centre of gravity model?
* Change the way the camera movement works
* Add rotation for boids (match velocity)
* Add MC-Edit-style GUI
    * add swarms (by dragging and dropping?)
	* tweak settings on the fly


## Admin

* Fill in README
* Write some unit tests (see Observable folder on home PC)
* Start report paint-by-numbers style (top-down)


## Misc

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