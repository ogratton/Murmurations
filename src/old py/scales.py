from numpy import array, roll

s = 1  # semitone
t = 2  # tone
p = 3  # tone+

aeolian    = array([t, s, t, t, s, t, t])
locrian    = roll(aeolian, -1)
ionian     = roll(aeolian, -2)
dorian     = roll(aeolian, -3)
phrygian   = roll(aeolian, -4)
lydian     = roll(aeolian, -5)
mixolydian = roll(aeolian, -6)

major   = ionian
nat_min = aeolian
har_min = [t, s, t, t, s, p, s]
mel_min = [t, s, t, t, t, t, s]
blues   = [p, t, s, s, p, t]
min_pen = [p, t, t, p, t]
chrom   = [s]
maj_arp = [4, 3, 5]
maj_sev = [4, 3, 3, 2]
min_arp = [3, 4, 5]
whole   = [t, t, t, t, t]
persian = [s, p, s, s, t, p, s]
satie   = [t, s, p, s, t, p]      # from gnossienne no. 3 (min arp interlaced with the maj arp of one tone above root)


def gen_range(mode=aeolian, lowest=60, note_range=48):
    """
    Generate a list of midi notes in the desired mode, treating the lowest note as the tonic
    :param mode: musical mode, in the form of a list of intervals
    :param lowest: midi number of tonic (and lowest) note
    :param note_range: range in the chromatic scale (not the one we are making)
    :return:
    """
    # TODO have tonic as optional separate variable so lowest != tonic
    # start with lowest note
    notes = [lowest]
    previous_note = lowest
    i = 0
    while previous_note < (lowest+note_range):
        cur_note = previous_note + mode[i % len(mode)]
        notes.append(cur_note)
        previous_note = cur_note
        i += 1
    return notes
