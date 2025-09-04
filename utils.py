import numpy as np
import numpy.typing as npt
from itertools import product


def get_first(generator):
    for item in generator:
        return item


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


if __name__ == "__main__":
    print(
        text_board(
            np.array(
                [
                    [8, -1, -1, -1, -1, -1, -1, -1, -1],
                    [-1, -1, 3, 6, -1, -1, -1, -1, -1],
                    [-1, 7, -1, -1, 9, -1, 2, -1, -1],
                    [-1, 5, -1, -1, -1, 7, -1, -1, -1],
                    [-1, -1, -1, -1, 4, 5, 7, -1, -1],
                    [-1, -1, -1, 1, -1, -1, -1, 3, -1],
                    [-1, -1, 1, -1, -1, -1, -1, 6, 8],
                    [-1, -1, 8, 5, -1, -1, -1, 1, -1],
                    [-1, 9, -1, -1, -1, -1, 4, -1, -1],
                ]
            )
        )
    )
