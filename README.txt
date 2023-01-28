Usage:

python3 maxine.py
Runs in stand-alone mode (default).

python3 maxine.py --datadir DIR
Run Maxine's Quest based on some stored current data.

python3 maxine.py --live Jonathan|Kent|Hackerboard4|Hackerboard5
Connect to Lilith server to play using the live current and joystick data from a MR Games Console(TM).

Optional player argument (defaults to maxine).
python3 maxine.py --player maxine|console
Lets the user play as maxine or the console player.

Optional level argument (defaults to 1).
python3 maxine.py --level [1-6]
Choose the starting level. Level 1 is mushrooms, level 2 is MidJourney monsters, levels 3-5 feature the Gurk Cannon, and level 6 is the Dragon Tyrant roguelike maze game. Levels 7 and 8 are mazes with an exponential world map (a bit like a fisheye view). Level 7 is medium size and Level 8 is huge.

Optional video argument (defaults to no video)
python3 maxine.py --video VIDEOFILE
Display a video file in the background. It must be around 640x360 or the game slows down.

Optional monster ratio argument (for maze levels).
python3 maxine.py --monster-ratio ZOMBIES,SNAKES,GHOSTS
Choose the number of each monster type that appears with every spike.

Optional doors argument (for maze levels).
python3 maxine.py --doors NUMBER
Choose the number of doors that appear with every spike.

