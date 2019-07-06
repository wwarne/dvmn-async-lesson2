import asyncio
import curses
import itertools
import random
import time

import global_vars
import settings
from curses_tools import draw_frame, get_frame_size, load_frame, read_controls
from explosion import explode
from game_scenario import PHRASES, get_garbage_delay_tics
from physics import update_speed
from space_garbage import fly_garbage, obstacles, obstacles_in_last_collisions

BORDER_SIZE = 1
STATUS_BAR_HEIGHT = 2


async def controls_writer(canvas):
    """Reads user's input and adds it to a queue."""
    while True:
        global_vars.controls_queue.append(read_controls(canvas))
        await asyncio.sleep(0)


async def sleep(tics=1):
    for _ in range(tics):
        await asyncio.sleep(0)


async def increase_year():
    """Coroutine helps years go by."""
    while True:
        await sleep(settings.TICS_PER_YEAR)
        if not global_vars.is_game_over:
            global_vars.year += 1


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
    await sleep(offset_tics)
    while True:
        canvas.addstr(row, column, symbol, curses.A_DIM)
        await sleep(20)

        canvas.addstr(row, column, symbol)
        await sleep(3)

        canvas.addstr(row, column, symbol, curses.A_BOLD)
        await sleep(5)

        canvas.addstr(row, column, symbol)
        await sleep(3)


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
        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                obstacles_in_last_collisions.append(obstacle)
                await explode(canvas, obstacle.row, obstacle.column)
                return
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
    max_row_num -= 2 * BORDER_SIZE  # 2 for borders
    max_column_num -= 2 * BORDER_SIZE
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


async def animate_spaceship_frame(frames):
    """Changes current spaceship frame."""
    for frame in itertools.cycle(frames):
        global_vars.spaceship_frame = frame
        await asyncio.sleep(0)


async def run_spaceship(canvas):
    max_row_num, max_column_num = canvas.getmaxyx()
    max_row_num -= BORDER_SIZE
    max_column_num -= BORDER_SIZE

    row_speed = col_speed = 0
    row, column = max_row_num // 2, max_column_num // 2

    spaceship_height, spaceship_width = get_frame_size(global_vars.spaceship_frame)

    while True:
        if len(global_vars.controls_queue):
            row_shift, column_shift, space_pressed = global_vars.controls_queue.pop(0)
        else:
            row_shift, column_shift, space_pressed = 0, 0, False
        if space_pressed and global_vars.year >= settings.PLASMA_GUN_YEAR:
            spacegun_pos_x = column + spaceship_width // 2
            spacegun_pos_y = row
            global_vars.coroutines.append(fire(canvas, spacegun_pos_y, spacegun_pos_x))

        row_speed, col_speed = update_speed(row_speed, col_speed, row_shift, column_shift)
        row += row_speed
        column += col_speed

        column_after_movement = column + spaceship_width
        row_after_movement = row + spaceship_height
        column = min(column_after_movement, max_column_num) - spaceship_width
        row = min(row_after_movement, max_row_num) - spaceship_height
        column = max(column, BORDER_SIZE)
        row = max(row, BORDER_SIZE)

        current_frame = global_vars.spaceship_frame
        draw_frame(canvas, row, column, current_frame)
        previous_frame = current_frame
        await asyncio.sleep(0)
        draw_frame(canvas, row, column, previous_frame, negative=True)

        for obstacle in obstacles:
            if obstacle.has_collision(row, column):
                frame_game_over = load_frame('frames/game_over.txt')
                global_vars.is_game_over = True
                await explode(canvas, row, column)
                global_vars.coroutines.append(show_game_over(canvas, frame_game_over))
                return


async def fill_orbit_with_garbage(canvas):
    """Spawn a lot of space garbage."""
    garbage_names = [
        'duck.txt',
        'hubble.txt',
        'lamp.txt',
        'trash_large.txt',
        'trash_small.txt',
        'trash_xl.txt'
    ]
    _, max_column_num = canvas.getmaxyx()

    frames = [load_frame(f'frames/garbage/{name}') for name in garbage_names]
    while True:
        garbage_timeout = get_garbage_delay_tics(global_vars.year)
        if garbage_timeout and not global_vars.is_game_over:
            current_trash_frame = random.choice(frames)
            _, trash_column_size = get_frame_size(current_trash_frame)
            random_column = random.randint(
                BORDER_SIZE,
                max_column_num - trash_column_size - BORDER_SIZE
            )
            global_vars.coroutines.append(
                fly_garbage(
                    canvas=canvas,
                    column=random_column,
                    garbage_frame=current_trash_frame,
                )
            )
        await sleep(garbage_timeout or 1)


async def show_game_over(canvas, frame):
    max_pos_y, max_pox_x = canvas.getmaxyx()
    message_size_y, message_size_x = get_frame_size(frame)
    message_pos_y = (max_pos_y // 2) - (message_size_y // 2)
    message_pos_x = (max_pox_x // 2) - (message_size_x // 2)
    while True:
        draw_frame(canvas, message_pos_y, message_pos_x, frame)
        await asyncio.sleep(0)


async def show_year(canvas):
    while True:
        message = f'{global_vars.year} {PHRASES.get(global_vars.year, "")}'
        canvas.addstr(1, 1, message)
        await sleep(settings.TICS_PER_YEAR)
        canvas.addstr(1, 1, ' ' * len(message))


def draw(canvas):
    canvas.nodelay(True)   # getch() will be non-blocking
    curses.curs_set(False)  # hide cursor

    max_row_num, max_column_num = canvas.getmaxyx()
    status_bar_begin_y = status_bar_begin_x = 0
    status_bar = canvas.derwin(STATUS_BAR_HEIGHT, max_column_num, status_bar_begin_y, status_bar_begin_x)
    game_area_height = max_row_num - STATUS_BAR_HEIGHT - BORDER_SIZE
    game_area_begin_y = STATUS_BAR_HEIGHT + BORDER_SIZE
    game_area_begin_x = 0
    game_area = canvas.derwin(game_area_height, max_column_num, game_area_begin_y, game_area_begin_x)
    game_area.border()

    spaceship_frames = (
        load_frame('frames/spacecraft/rocket_frame_1.txt'),
        load_frame('frames/spacecraft/rocket_frame_2.txt'),
    )

    global_vars.coroutines += generate_stars(game_area, number_of_stars=settings.NUMBER_OF_STARS)
    global_vars.coroutines.append(show_year(status_bar))
    global_vars.coroutines.append(fill_orbit_with_garbage(game_area))
    global_vars.coroutines.append(animate_spaceship_frame(spaceship_frames))
    global_vars.coroutines.append(run_spaceship(game_area))
    global_vars.coroutines.append(increase_year())
    global_vars.coroutines.append(controls_writer(canvas))
    while True:
        for coroutine in global_vars.coroutines.copy():
            try:
                coroutine.send(None)
            except StopIteration:
                global_vars.coroutines.remove(coroutine)
        game_area.refresh()
        game_area.border()  # re-draw the border because flying objects "eat" it.
        status_bar.refresh()
        time.sleep(settings.TIC_TIMEOUT)


if __name__ == '__main__':
    curses.update_lines_cols()
    curses.wrapper(draw)
