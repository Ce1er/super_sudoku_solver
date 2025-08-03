import numpy as np
import numpy.typing as npt
from sudoku import Board


class Human_Solver:
    def __init__(self, board: Board) -> None:
        self.candidates: npt.NDArray[np.bool] = board.get_candidates()  # 9x9x9
        # dimension 1 = number

    def _singles(self):
        types = {
            Board.adjacent_row: "row",
            Board.adjacent_column: "column",
            Board.adjacent_box: "box",
        }
        for coord in np.argwhere(self.candidates):
            num, row, column = coord
            for func, adjacency in types.items():
                if np.count_nonzero(func((row, column)) & self.candidates[num]) == 1:
                    print(
                        f"Cell ({row+1}, {column+1}) is {num+1} because there are no other {num+1}s in the {adjacency}"
                    )


if __name__ == "__main__":
    board = Board(
        ".18....7..7...19...6.85.12.6..7..3..7..51..8.8.4..97.5.47.98.5...26.5.3...6...24."
        # "................................................................................1"
        # "..............................................................................321"
    )

    board.auto_normal()

    human = Human_Solver(board)

    human._singles()
