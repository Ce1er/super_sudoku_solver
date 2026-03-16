import re
from custom_types import Candidates, Cells, Coord
import human_solver
from time import time

# TODO: make techniques work
# could have some circular import problems so avoid relying on sudoku.py too much in techniques.py
# import techniques

from typing import Optional, Generator
import numpy as np
import numpy.typing as npt
import dlx_solver as dlx
import techniques
from human_solver import Action

from save_manager import Puzzle
import np_candidates as npc

from utils import get_first, text_hints


class InvalidBoard(Exception):
    pass


class Board:
    """
    Represents board as a whole
    """

    def __init__(
        self, puzzle: Puzzle, allow_mistakes: bool = False, one_solution: bool = True
    ) -> None:
        r"""
        Args:
            cells: Represents starting clues. Matches regex ^[0-9\.]{81}$
        """
        self._puzzle = puzzle
        self.allow_mistakes = allow_mistakes
        self.one_solution = one_solution

        AUTONORMAL = True  # TODO: move this to somewhere else. Idealing reading from a settings.* file.
        if AUTONORMAL:
            self.all_normal()

    def remove_candidates(
        self, candidates: npt.NDArray[np.bool], type: str = "normal"
    ) -> None:
        """
        Args:
            candidates: 9x9x9
            type: Refers to types in key of Board.hints. Default normal, highlight and strikethrough.
        """
        new = (~candidates) & self._puzzle.candidates
        coords = np.argwhere(self.solution)
        # TODO: find a way to do this without iteration, using np stuff instead.
        for coord in coords:
            if not new[self.solution[coord], *coord]:
                raise InvalidBoard("Removed candidate which is solution for cell")
        self._puzzle.candidates = new

    @property
    def cells(self):
        return self._puzzle.cells

    @property
    def clues(self):
        return self._puzzle.clues

    def is_clue(self, coord: Coord) -> bool:
        return self._puzzle.clues[*coord] != -1

    @property
    def guesses(self):
        return self._puzzle.guesses

    @property
    def candidates(self):
        return self._puzzle.candidates

    def add_cells(self, cells: Cells):
        """
        Args:
            cells: 9x9 array where each element is between 0 and 8 inclusive. -1 to not add anything.
        """
        # Keep current guesses and add new ones
        new = np.where(self._puzzle.guesses != -1, self._puzzle.guesses, cells)

        if not self.allow_mistakes:
            if self.one_solution:
                # Any coord where new != -1 must be eq to self.solution
                # When new == -1 it isn't a guess so that coord is always valid
                x = np.logical_or.reduce(
                    np.array([new == -1, new == self.solution]), axis=0, dtype=np.bool
                )
                if not x.all():
                    raise InvalidBoard("Added cells leads to unsolvable board state.")
            else:
                # TODO: Do I even want multiple solution support?
                raise NotImplementedError
        self._puzzle.guesses = new

    def all_normal(self) -> None:
        """
        Sets all normal hints to True
        """
        new: Candidates = np.full((9, 9, 9), True, dtype=np.bool)
        for coord in np.argwhere(self._puzzle.clues != -1):
            new[:, *coord] = False
        self._puzzle.candidates = new
        print(text_hints(self._puzzle.candidates))

    def auto_normal(self) -> None:
        """
        Remove candidates from cells if they have a number adjacent to them
        """
        print(text_hints(self._puzzle.candidates))
        mask = np.full((9, 9, 9), False, dtype=bool)
        cells = self._puzzle.cells
        for cell in np.argwhere(cells != -1):
            num = cells[*cell]
            mask[num] = npc.adjacent(cell) | mask[num]

            # Remove all hints if a cell is there
            mask[:, cell[0], cell[1]] = True

        print(text_hints(mask))
        # If candidates have already been removed keep them that way
        self._puzzle.candidates = (~mask) & self._puzzle.candidates

    @staticmethod
    def _row_add(column: int, row: int, value: int) -> list[int]:
        """
        Helper for create_matrix that creates a single row
        """
        return [
            9 * row + column,  # Cell constraint
            81 + 9 * row + value,  # Row constraint
            162 + 9 * column + value,  # Column constraint
            243 + 9 * (3 * (row // 3) + (column // 3)) + value,  # Box constraint
        ]

    def create_matrix(self) -> dlx.Matrix:
        """
        Labels are constraints
        Labels 0-80 one number per cell
        Labels 81-161 each digit once per row
        Labels 162-242 each digit once per column
        Labels 243-323 each digit once per box
        """
        rows = []

        x = 0
        y = 0
        # Number of rows = clues + 9 * (81-clues)
        # for column, row, value in self.cells.get_cells(include_empty=True):
        cells = self._puzzle.cells
        for column, row in np.argwhere(cells > -2):
            value = cells[column, row]
            if value != -1:
                x += 1
                rows.append(self._row_add(int(column), int(row), int(value)))
            else:
                for i in range(9):
                    y += 1
                    rows.append(self._row_add(int(column), int(row), i))

        # Only make labels for the ones referenced in rows
        labels = list(set(item for row in rows for item in row))
        return dlx.Matrix(labels, rows)

    @staticmethod
    def extract_from_matrix(solution: list[list[int]]) -> npt.NDArray[np.int8]:
        """
        Args:
            solution: a list of lists of labels from DLX matrix
        Returns:
            9x9 np.NDArray with full solution
        """
        board: npt.NDArray = np.full((9, 9), -1, dtype=np.int8)

        # Convert DLX matrix representation to 9x9 2D list[list[int]]
        count = 0
        for row in solution:
            row.sort()  # Probably unnecessary
            # Coordinates
            x = row[0] % 9
            y = row[0] // 9

            value = (row[1] - 81) % 9
            board[x][y] = value
            count += 1
        return board

    def solve(
        self,
        # , one_solution: bool = True
    ) -> Generator[npt.NDArray[np.int8], None, None]:
        """
        Solve the board
        Returns:
            -1 if no solutions otherwise the number of solutions.
        """
        matrix = self.create_matrix()
        for solution in matrix.generate_solutions():
            yield self.extract_from_matrix(solution)

    @property
    def solution(self):
        # Could store solution as an attribute but this takes at most like 10ms so idc=
        # solution = get_first(self.solve())
        first = True
        solution = None
        for s in self.solve():
            if not first:
                if self.one_solution:
                    raise InvalidBoard("Board has multiple solutions")
                else:
                    # Return the first solution if there are several.
                    # If you want them all call solve() directly.
                    break
            solution = s
            first = False
        if solution is None:
            raise InvalidBoard("Board has no solutions")
        return solution

    def hint(self):  # -> Generator[human_solver.Technique]:
        for technique in techniques.TECHNIQUES:
            technique = technique(self.candidates, self.clues, self.guesses)
            yield from technique.find()

    def apply_action(self, action: Action) -> None:
        """
        Modify cells and candidates in place based on Action
        Args:
            action: the Action to apply
        """
        if (x := action.cells) is not None:
            self.add_cells(x)

        if (x := action.candidates) is not None:
            self.remove_candidates(x)

    def auto_solve(self):
        """
        Set the cells to the values they should be when solved
        """
        for solution in self.solve():
            self._puzzle.guesses = np.where(
                self._puzzle.clues != -1, self._puzzle.clues, solution
            )


# board = Board(
#     ".83..241.2.4..5....1..74.283..49.15...7.1...69..753.8.84....6..5...4..31136.2.5..",
# )
# # Solution = "783962415294185763615374928328496157457218396961753284849531672572649831136827549"
# for solution in board.solve():
#     print(solution)
#
# exit()

# board = Board(
#     ".5..8.......3...9.21..9...862.7..1....5.2......3.....6.....47..89..3...1..6......",
# )
# for solution in board.solve():
#     print(solution)

if __name__ == "__main__":
    # board = Board(
    #     ".................................................................................",
    # )
    # start = time()
    # i = 0
    # for solution in board.solve():
    #     i += 1
    #     if i > 100_000:
    #         break
    #     # print(solution)
    # print(time() - start)

    # print("1, 2")
    # print(board.adjacent((1, 2)))
    # print("2, 2")
    # print(board.adjacent((2, 2)))
    # print("1, 1")
    # print(board.adjacent((1, 1)))
    # print("0, 0")
    # print(board.adjacent((0, 0)))
    # print("5, 8")
    # print(board.adjacent((5, 8)))

    from uuid import uuid7

    puzzle = Puzzle(
        str(uuid7()),
        ".5..8.......3...9.21..9...862.7..1....5.2......3.....6.....47..89..3...1..6......",
        "easy",
    )
    board = Board(puzzle)
    board.solve()

# TODO: just make literally everything 0-based.
