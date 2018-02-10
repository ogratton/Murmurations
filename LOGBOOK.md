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
	* This allows for more melodic interest, as boids now follow less predictable rising and falling paths
* Defined parametrically defined paths for attractors to follow
	* The paths are defined somewhat randomly, but not randomly enough for my liking
	* They currently all take a circuit of the entire space, but it may be good to restrict some to tighter loops

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
* Implemented predators, then removed them as they were very laggy
* Implemented stigmergy between swarms and then removed it (as above)
	* led to feeback loop, technique needs rethinking
* Made interpreters customisable by JSON files
	* Next: GUI sliders etc.
* Rewritten main interpreter module
* Added more dimensions in the swarm simulation (for pan, note length etc.)
* Discovered how to link to proper VST synths etc. on windows (requires no code change except midiout port)
* Experimented with Cython on Linux and it sped up quite a lot, but can't get it to work on Windows

### 2018/01/12 - Week 16

* Added Monophonic interpreter (second coming of NaiveSequencer)
	* produces monophonic melodies as opposed to a vomit of notes
* Reading and write-up plan

### 2018/01/19 - Week 17

* Implemented recording real-time performances to MIDI files (and then to dodgy sheet music)
* Made some basic GUIs with PyQt5 (yet to be integrated)
* Found new soundfont, which makes everything sound a bit nicer
* Made models of absolute scale to emphasise importance of cube size on sound

### 2018/01/26 - Week 18

* Nothing...

### 2018/02/02 - Week 20

* Fixed articulation dimension
* Boids only play when near attractors so as to cut down on the mess of notes
* Made random notes generator to compare my interpreters and guide it away from randomness and towards structure/niceness :)
* Worked on the midi-input mode (improvising with a real person)
	* need to work out how to make it less like a mimic though

### 2018/02/09 - Week 21

* Properly started work on stigmergy (inter-swarm communication)
* Attractors become repulsors if a boid is in the lower half of the 5th dimension (an arbitrary design choice but means that using only one attractor is no longer guaranteed chromaticism)
* Tidied up code so I don't have to change stuff in 5 different places every time I want to change settings
* Minor improvements and bug fixes