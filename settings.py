"""
Settings and constants.
"""

# timeout between coroutines' list traversal
# used because we can only use asyncio.sleep(0) with current event loop
TIC_TIMEOUT = 0.1

# Number of stars on screen.
NUMBER_OF_STARS = 100

TICS_PER_YEAR = 15

PLASMA_GUN_YEAR = 2020
