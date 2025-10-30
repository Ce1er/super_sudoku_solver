import numpy as np
import numpy.typing as npt
from sudoku import Board
from itertools import product


def valid_sudoku(board: npt.NDArray[np.int8]):
    if board.shape != (9, 9):
        return False

    for num in range(9):
        mask = board == num
        for coord in np.argwhere(mask):
            x = coord[0]
            y = coord[1]
            if np.count_nonzero(mask & Board.adjacent((x, y))) != 1:
                return False

    adjacencies = [Board.adjacent_row, Board.adjacent_box, Board.adjacent_column]
    for x, y in product(range(9), repeat=2):
        for adjacency in adjacencies:
            nums = board[adjacency((x, y))]
            for i in range(9):
                if np.count_nonzero(nums == i) != 1:
                    return False

    return True


if __name__ == "__main__":
    board = Board(
        "...........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4..",
    )
    for solution in board.solve():
        print(valid_sudoku(solution))
