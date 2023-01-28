import argparse

parser = argparse.ArgumentParser(description='Play Maxine\'s Quest.')
parser.add_argument('--datadir', action='store')
parser.add_argument('--live', action='store')
parser.add_argument('--player', action='store')
parser.add_argument('--level', action='store')
# This will be the default when a video isn't specified
#parser.add_argument('--show-background', action='store_true')
parser.add_argument('--video', action='store')
parser.add_argument('--monster-ratio', action='store')
