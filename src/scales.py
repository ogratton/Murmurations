from numpy import r_, roll

k = 0  # keynote
s = 1  # semitone
t = 2  # tone
p = 3  # tone+

aeolian    = r_[t, s, t, t, s, t, t]
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
min_arp = [3, 4, 5]
whole   = [t, t, t, t, t]
persian = [s, p, s, s, t, p, s]

def gen_range(mode=aeolian, lowest=60, note_range=48):
    # start with lowest note
    notes = [lowest]
    previous_note = lowest
    i = 0
    while previous_note < (lowest+note_range):
        cur_note = previous_note + mode[i%len(mode)]
        notes.append(cur_note)
        previous_note = cur_note
        i += 1
    return notes
