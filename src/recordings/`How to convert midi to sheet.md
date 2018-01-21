Once the midi file is generated from LogToMidi.pyw, run the following command (or the equivalent on your machine):

python2 "D:\Program Files (x86)\LilyPond\usr\bin\midi2ly.py" -o "output.ly" ".\output.mid"

Then compile the .ly file with LilyPond to receive the disappointing results.
WARNING: midi file is overwritten by LilyPond if you just double-click the .ly and are using the same filenames


(TODO: write another .py to run this. Will need to read command from a separate file for cross-platform compat.)