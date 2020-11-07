import os

from .SwarmMain import main

if __name__ == "__main__":

    # on linux I use port 1, windows I use port 1
    # change to whichever port you need
    out_port = 0
    in_port = 0

    if os.name != "nt":
        out_port = 1
        in_port = 0

    main(out_port, in_port)
