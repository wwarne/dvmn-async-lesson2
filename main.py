import asyncio
import curses
import itertools
import random
import time

import settings
from curses_tools import draw_frame, get_frame_size, read_controls


async def blink(canvas, row, column, symbol='*', offset_tics=0):
    """
    Draw animated symbol by provided coordinates.

    :param canvas:  window object from curses
    :param row: number of row
    :param column: number of column
    :param symbol: symbol to draw
    :param offset_tics: delay before starting animation so it won't start at the same time as others
    :return: coroutine for animate symbol at row x column
    """
    for _ in range(offset_tics):
        await asyncio.sleep(0)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        for _ in range(20):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        for _ in range(5):
            await asyncio.sleep(0)

        canvas.addstr(row, column, symbol)
        for _ in range(3):
            await asyncio.sleep(0)


async def fire(canvas, start_row, start_column, rows_speed=-0.3, columns_speed=0):
    """Display animation of gun shot. Direction and speed can be specified."""

    row, column = start_row, start_column

    canvas.addstr(round(row), round(column), '*')
    await asyncio.sleep(0)

    canvas.addstr(round(row), round(column), 'O')
    await asyncio.sleep(0)
    canvas.addstr(round(row), round(column), ' ')

    row += rows_speed
    column += columns_speed

    symbol = '-' if columns_speed else '|'

    rows, columns = canvas.getmaxyx()
    max_row, max_column = rows - 1, columns - 1

    # curses.beep()

    while 0 < row < max_row and 0 < column < max_column:
        canvas.addstr(round(row), round(column), symbol)
        await asyncio.sleep(0)
        canvas.addstr(round(row), round(column), ' ')
        row += rows_speed
        column += columns_speed


def generate_stars(canvas, number_of_stars):
    """
    Generate array of stars.

    Each stars has unique coordinates. The more stars - the more CPU load.
    And with animated star as every symbol on screen it's too much.
    What's why maximum number of stars is limited to 50% of screen space.

    :param canvas: window object from curses
    :param number_of_stars: number of stars
    :return: list with coroutines
    """
    max_row_num, max_column_num = canvas.getmaxyx()
    max_row_num -= 2  # 2 for borders
    max_column_num -= 2
    stars = []
    maximum_stars = (max_row_num * max_column_num) // 2
    if number_of_stars > maximum_stars:
        number_of_stars = maximum_stars
    used_coordinates = []
    while len(stars) < number_of_stars:
        column = random.randint(1, max_column_num)
        row = random.randint(1, max_row_num)
        if (row, column) in used_coordinates:
            continue
        star_type = random.choice('+*.:')
        time_offset = random.randint(0, 30)
        stars.append(blink(canvas, row, column, star_type, time_offset))
        used_coordinates.append((row, column))
    return stars


def load_frame(filepath):
    """Load animation frame from the file."""
    with open(filepath, mode='r', encoding='utf-8') as f:
        return f.read()


async def animate_spaceship(canvas, row, column, frames):
    max_row_num, max_column_num = canvas.getmaxyx()
    for frame in itertools.cycle(frames):
        draw_frame(canvas, row, column, frame)
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, frame, negative=True)

        row_shift, column_shift, space_pressed = read_controls(canvas)
        # checking for collisions with screen borders
        frame_rows, frame_columns = get_frame_size(frame)
        if 0 < row + row_shift < max_row_num - frame_rows:
            row += row_shift
        if 0 < column + column_shift < max_column_num - frame_columns:
            column += column_shift


def draw(canvas):
    canvas.border()  # draw border around screen
    canvas.nodelay(True)   # getch() will be non-blocking
    curses.curs_set(False)  # hide cursor

    max_row_num, max_column_num = canvas.getmaxyx()
    coroutines = []
    coroutines += generate_stars(canvas, number_of_stars=settings.NUMBER_OF_STARS)
    frames = (
        load_frame('frames/rocket_frame_1.txt'),
        load_frame('frames/rocket_frame_2.txt'),
    )
    spaceship = animate_spaceship(canvas, max_row_num//2, max_column_num//2, frames)
    coroutines.append(spaceship)
    while True:
        for coroutine in coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                coroutines.remove(coroutine)
        canvas.refresh()
        time.sleep(settings.TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
