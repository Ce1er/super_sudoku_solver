import numpy as np
import numpy.typing as npt
from sudoku import Board
from itertools import product


class Human_Solver:
    def __init__(self, board: Board) -> None:
        self.candidates: npt.NDArray[np.bool] = board.get_candidates()  # 9x9x9

    def _singles(self):
        for x, y in product(range(0, 9), repeat=2):
            for num in range(1, 10):
                if not self.candidates[num - 1][y][x]:
                    continue
                if True not in (self.candidates[num - 1][x - 1, :]):
                    print(
                        f"Cell ({x},{y}) is {num} because there are no other {num}s in the row"
                    )
                if True not in (self.candidates[num - 1][:, y - 1]):
                    print("Single for row")
                if True not in (
                    self.candidates[num - 1][
                        3 * ((x - 1) // 3) : 3 * ((x - 1) // 3) + 3,
                        3 * ((y - 1) // 3) : 3 * ((y - 1) // 3) + 3,
                    ]
                ):
                    print("Single for box")


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
