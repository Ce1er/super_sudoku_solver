import numpy as np
import numpy.typing as npt
from itertools import product


def text_board(board: npt.NDArray[np.int8]):
    # TODO: rewrite this whole function. It works but has no validation and isn't very readable.
    top = "╔═══╤═══╤═══╦═══╤═══╤═══╦═══╤═══╤═══╗"
    middle_big = "╠═══╪═══╪═══╬═══╪═══╪═══╬═══╪═══╪═══╣"
    middle_small = "╟───┼───┼───╫───┼───┼───╫───┼───┼───╢"
    number_row = "║ {} │ {} │ {} ║ {} │ {} │ {} ║ {} │ {} │ {} ║"
    bottom = "╚═══╧═══╧═══╩═══╧═══╧═══╩═══╧═══╧═══╝"

    s = ""
    for row in range(9):
        s += (
            (top if row == 0 else (middle_big if row in (3, 6) else middle_small))
            + "\n"
            + number_row.format(
                *list(map(lambda x: x if int(x) != -1 else " ", board[row]))
            )
            + "\n"
        )
    return s + bottom


def text_hints(hints: npt.NDArray[np.bool]):
    """Args:
    hints: dimensions are 9x9x9 for num X row X column
    """
    top = "╔═══╤═══╤═══╦═══╤═══╤═══╦═══╤═══╤═══╗"
    middle_big = "╠═══╪═══╪═══╬═══╪═══╪═══╬═══╪═══╪═══╣"
    middle_small = "╟───┼───┼───╫───┼───┼───╫───┼───┼───╢"
    number_row = "║{}{}{}│{}{}{}│{}{}{}║{}{}{}│{}{}{}│{}{}{}║{}{}{}│{}{}{}│{}{}{}║"
    bottom = "╚═══╧═══╧═══╩═══╧═══╧═══╩═══╧═══╧═══╝"

    def num_row(
        nums: range,
    ):
        return number_row.format(
            *list(
                map(
                    str,
                    np.array(
                        [
                            [str(x + 1) if hints[x, row, y] else " " for x in nums]
                            for y in range(9)
                        ]
                    ).flatten(),
                )
            )
        )

    s = ""
    for row in range(9):
        s += (
            (top if row == 0 else (middle_big if row in (3, 6) else middle_small))
            + "\n"
            + num_row(range(3))
            + "\n"
            + num_row(range(3, 6))
            + "\n"
            + num_row(range(6, 9))
            + "\n"
        )
    return s + bottom
