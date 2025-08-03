import numpy as np
import numpy.typing as npt
from sudoku import Board
from itertools import product


class Human_Solver:
    def __init__(self, board: Board) -> None:
        self.candidates: npt.NDArray[np.bool] = board.get_candidates()  # 9x9x9
        # dimension 1 = number

    def _singles(self):
        print(self.candidates)
        for coord in np.argwhere(np.full((9, 9), True, dtype=bool)):
            row, column = coord[0], coord[1]
            for num in range(1, 10):
                if (
                    np.count_nonzero(
                        Board.adjacent_row((row, column)) & self.candidates[num - 1]
                    )
                    == 1
                    and self.candidates[num - 1, row, column]
                ):
                    print(
                        f"Cell ({row+1}, {column+1}) is {num} because there are no other {num}s in the row."
                    )

                if (
                    np.count_nonzero(
                        Board.adjacent_column((row, column)) & self.candidates[num - 1]
                    )
                    == 1
                    and self.candidates[num - 1, row, column]
                ):
                    print(
                        f"Cell ({row+1}, {column+1}) is {num} because there are no other {num}s in the column."
                    )

                if (
                    np.count_nonzero(
                        Board.adjacent_box((row, column)) & self.candidates[num - 1]
                    )
                    == 1
                    and self.candidates[num - 1, row, column]
                ):
                    print(
                        f"Cell ({row+1}, {column+1}) is {num} because there are no other {num}s in the box."
                    )


if __name__ == "__main__":
    board = Board(
        ".18....7..7...19...6.85.12.6..7..3..7..51..8.8.4..97.5.47.98.5...26.5.3...6...24."
        # "................................................................................1"
        # "..............................................................................321"
    )

    board.auto_normal()
    # TODO: make it work. Probably off by one error related with coordinates sometimes 0 based and sometimes 1 based

    # print(board.hints["normal"].get_hints())

    # print(board.get_candidates())

    human = Human_Solver(board)

    human._singles()
