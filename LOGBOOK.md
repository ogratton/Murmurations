# PROJECT LOGBOOK

### 2017/09/29 - Week 1

* Researching topics for project.
* Looking particularly at Dr Tim Blackwell's "Swarming and Music" 

### 2017/10/06 - Week 2

* Decided on swarm music project
* Made simple swarm demos in Unity, Processing, and Python to decide which to use

### 2017/10/13 - Week 3

* Continued research and followed some tutorials for 3D graphics in python

### 2017/10/20 - Week 4

* Written basic swarm code in Python with OpenGL
* Completed Project Proposal

### 2017/10/27 - Week 5

* Refactored all current work into neater class structures
* Colour-coded swarms
* Added docstrings
* Added centre of mass calculation as first step toward sound
* Trialled Observer pattern but need more of a 'polling' approach (only get COM when needed)
* Added basic sound interpretation

### 2017/11/03 - Week 6

* Added attractors for the swarm agents
* Changed visual code from Pygame to Pyglet
	* Boids are now cubes, and attractors spheres, rather than lines
	* User can now move camera around in 3D space and snap to objects
* (Changed normal constants to prevent "overfitting" of sorts)
* Converted to numpy's r_ vector class, which doesn't seem that much faster than my own...

### 2017/11/10 - Week 7

* Added ChordInterpreter which treats each boid as a note
* Made .ini file to allow for easier tweaking of variables
* Realised that default class values are set at run-time (hence time bugs)
* Implemented beat and scale snapping
* Added lots of videos of system


### 2017/11/17 - Week 8

* Reading for Literature Review

### 2017/11/24 - Week 9

* Changed models around
	* "cube" is shown as sphere (due to how the Constraint rule is currently implemented)
	* attractors are cubes
	* boids are pyramids
* Attempted showing the boid's direction, but it is slightly off
* Allowed for multiple attractors at once
* Defined parametrically defined paths for attractors to follow

### 2017/12/01 - Week 10

* Wrote most of literature review
* Added snapping to ChordInterpreter
* Implements bounding box option (before was technically a sphere)
* Added many more videos

### 2017/12/08 - Week 11

* Nothing...

### 2017/12 - Christmas Holidays

* Implemented and then decided against bin-lattice spatial subdivision as it is not efficient for the number of boids I am using. Also, if the number of dimensions increases, BLSS will get pretty expensive, whereas norm() scales better
* Revised swarm rules and fixed jerky attractor attraction bug
* Added MIDI input attractor mode, which allows a user to place attractors via MIDI message
