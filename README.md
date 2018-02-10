# Murmurations
3rd Year Computer Science Final Project


## Dependencies:

* Python 3
* python-rtmidi
* pyglet
* PyQt5 (for settings GUI only)

## How to run:

Run SwarmMain.py and hope for the best.

The settings GUI is not yet implemented, so customisation must be done manually in the following places:
* config.ini
    * for swarm rules and attractor modes and the like
* /presets/*.json
    * for interpreter specific settings
    * new ones can be added and used by editing SwarmMain.py
* SwarmMain.py
    * can add new swarms and change instruments and all sorts

It's all a bit messy around there though, so here's hoping I get the GUI sorted
