"""
Settings and constants.
"""
from pathlib import Path

# timeout between coroutines' list traversal
# used because we can only use asyncio.sleep(0) with current event loop
TIC_TIMEOUT = 0.1

# Number of stars on screen.
NUMBER_OF_STARS = 100

TICS_PER_YEAR = 15

PLASMA_GUN_YEAR = 2020

BASE_DIR = Path(__file__).resolve().parent

FRAMES_DIR = BASE_DIR.joinpath('frames')

GARBAGE_FRAMES_DIR = FRAMES_DIR.joinpath('garbage')

SPACECRAFT_FRAMES_DIR = FRAMES_DIR.joinpath('spacecraft')

GAME_OVER_FRAME_PATH = FRAMES_DIR.joinpath('game_over.txt')

# You can comment out some names if you don't want to see particular garbage objects.
# Or you can add the new ones.
GARBAGE_PATHS = [
    GARBAGE_FRAMES_DIR.joinpath('duck.txt'),
    GARBAGE_FRAMES_DIR.joinpath('hubble.txt'),
    GARBAGE_FRAMES_DIR.joinpath('lamp.txt'),
    GARBAGE_FRAMES_DIR.joinpath('trash_large.txt'),
    GARBAGE_FRAMES_DIR.joinpath('trash_small.txt'),
    GARBAGE_FRAMES_DIR.joinpath('trash_xl.txt'),
]

SPACECRAFT_PATHS = [
    SPACECRAFT_FRAMES_DIR.joinpath('rocket_frame_1.txt'),
    SPACECRAFT_FRAMES_DIR.joinpath('rocket_frame_2.txt'),
]

SPACECRAFT_FLAME_PATHS = [
    SPACECRAFT_FRAMES_DIR.joinpath('flame_1.txt'),
    SPACECRAFT_FRAMES_DIR.joinpath('flame_2.txt'),
]
