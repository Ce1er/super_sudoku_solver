import re
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


# TODO: deprecate this class. Merge with Board.
class Cells:
    """
    Attributes:
        _clues: the given numbers in a puzzle. e.g. 53..7....6..195... for first 2 rows of a puzzle.
        cells: the union of the given cells and guesses.
    """

    _clues: npt.NDArray[np.int8]
    _cells: npt.NDArray[np.int8]

    def __init__(self, clues: str) -> None:
        # TODO: take clues and guesses seperately
        r"""
        Args:
            clues: given clues of puzzle. Matches regex ^[1-9\.]{81}$
        """
        assert re.match(r"^[1-9\.]{81}", clues), "Invalid clues given to Cells object"
        values = [-1 if clue == "." else int(clue) - 1 for clue in clues]
        self._clues = np.array(values, dtype=np.int8).reshape((9, 9))
        self._clues.flags.writeable = False

        self._cells = np.copy(self._clues)


    def is_clue(self, coord: npt.NDArray[np.int8]) -> bool:
        """
        Args:
            coord: shape (2,)
        Returns:
            If there is a clue at coord
        """
        return self._clues[*coord] != -1

    def add_cell(self, coordinate: tuple[int, int], value: int) -> None:
        """
        Adds cells with the most annoying non-numpy input possible. Will deprecate soon.
        """
        self._cells[*coordinate] = value

    def add_cells(self, cells: npt.NDArray[np.int8]):
        for coord in np.argwhere(cells != -1):
            self._cells[coord[0], coord[1]] = cells[*coord]

    @property
    def cells(self):
        return self._cells

    @property
    def clues(self):
        return self._clues

    @property
    def guesses(self):
        return np.where(self._clues == -1, self.cells, -1)

class Hints:
    """
    Attributes:
        hints: 9x9x9 boolean array. First dimension is num, second is row, third is col
    """

    def __init__(
        self,
        rgba: tuple[int, int, int, int],
        strikethrough: Optional[tuple[int, int, int, int]] = None,
        candidate: bool = True,
    ) -> None:
        """
        Args:
            hints: a list of dictionaries with the keys "coordinate" and "values"
                where the value of "coordinate" is a tuple containing the cartesian coordinate
                and "values" is a list of the values at that coordinate
            rgba: tuple with numbers from 0-255 representing red, green, blue and alpha
            candidate: True if hint array represents possible candidates
        """
        self._hints: npt.NDArray[np.bool] = np.full((9, 9, 9), False, dtype=bool)
        self._rgba: tuple[int, int, int, int] = rgba
        self._candidate: bool = candidate
        self._strikethrough: Optional[tuple[int, int, int, int]] = strikethrough

    @property
    def hints(self):
        return self._hints

    @property
    def rgba(self):
        return self._rgba

    @property
    def candidate(self):
        return self._candidate

    @property
    def strikethrough(self):
        return self._strikethrough

    def is_candidate(self) -> bool:
        """
        Returns:
            if this type of hint represents candidates or not
        """
        return self._candidate

    def add_hints(self, hints: npt.NDArray[np.bool]) -> None:
        """
        Args:
            hints: 9x9x9 arr of cands to add
        """
        self._hints = self._hints | hints

    def remove_hints(self, hints: npt.NDArray[np.bool]) -> None:
        """
        Args:
            hints: 9x9x9 arr of cands to add
        """
        self._hints = (~hints) & self._hints


class Board:
    """
    Represents board as a whole
    """

    # TODO: Use this instead
    # def __init__(
    #     self,
    #     clues: npt.NDArray[np.int8],
    #     guesses: Optional[npt.NDArray[np.int8]] = None,
    #     hints: Optional[dict[str, Hints]] = None, # Maybe take the data to create hints object instead
    # ):
    #     self.clues = clues
    #
    #     if guesses:
    #         self.guesses = guesses
    #     else:
    #         self.guesses = np.full((9, 9), -1, dtype=np.int8)
    #
    #     if hints:
    #         self.hints = hints
    #     else:
    #         self.hints = {
    #             "normal": Hints((146, 153, 166, 255)),
    #             "highlighted": Hints((66, 197, 212, 255)),
    #             "strikethrough": Hints((146, 153, 166, 255), (214, 41, 32, 255), False),
    #         }  # TODO: Store this information in a settings file

    def __init__(
        self,
        cells: str,
    ) -> None:
        r"""
        Args:
            cells: Represents starting clues. Matches regex ^[0-9\.]{81}$
        """
        assert re.match(r"^[0-9\.]{81}", cells), "Invalid clues given to Cells object"
        self._cells = Cells(cells)

        self._hints: dict[str, Hints] = {
            "normal": Hints((146, 153, 166, 255)),
            "highlighted": Hints((66, 197, 212, 255)),
            "strikethrough": Hints((146, 153, 166, 255), (214, 41, 32, 255), False),
        }

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
        self._hints[type].remove_hints(candidates)

    def is_clue(self, coord: npt.NDArray[np.int8]) -> bool:
        """
        Args:
            coord: shape (2,)
        Returns:
            If there is a clue at coord
        """
        return self._cells.is_clue(coord)

    @property
    def cells(self):
        return self._cells.cells

    @property
    def clues(self):
        return self._cells.clues

    @property
    def guesses(self):
        return self._cells.guesses

    @property
    def candidates(self):
        candidates = np.full((9, 9, 9), False, dtype=bool)

        for hint_type in self._hints.values():
            if hint_type.candidate:
                candidates = candidates | hint_type.hints
        return candidates

    def add_cells(self, cells: npt.NDArray[np.int8]):
        """
        Args:
            cells: 9x9 array where each element is between 0 and 8 inclusive. -1 to not add anything.
        """
        self._cells.add_cells(cells)

    def add_hint_type(
        self,
        name: str,
        rgba: tuple[int, int, int, int],
        strikethrough: Optional[tuple[int, int, int, int]],
    ) -> None:
        """
        Adds a new type of hint to self.hints
        Args:
            name: name of new hint type
            rgba: colour for highlighting
            strikethrough: whether there should be strikethrough over uses of this hint type
        """
        self._hints.update({name: Hints(rgba, strikethrough)})

    def remove_hint_type(self, name: str) -> None:
        """
        Removes a type of hint from self.hints
        """
        self._hints.pop(name)

    @staticmethod
    def adjacent_row(coords: tuple[int, int]) -> npt.NDArray[np.bool]:
        """
        Will be deprecated soon
        Args:
            coords: (row, column) with 0-based indexing
        Returns:
            Boolean array where True represents cells in same row to cell given
        """
        board = np.full((9, 9), False, dtype=bool)
        board[coords[0], :] = True  # Row
        return board

    @staticmethod
    def adjacent_column(coords: tuple[int, int]) -> npt.NDArray[np.bool]:
        """
        Will be deprecated soon
        Args:
            coords: (row, column) with 0-based indexing
        Returns:
            Boolean array where True represents cells in same column to cell given
        """
        board = np.full((9, 9), False, dtype=bool)
        board[:, coords[1]] = True  # Column
        return board

    @staticmethod
    def adjacent_box(coords: tuple[int, int]) -> npt.NDArray[np.bool]:
        """
        Will be deprecated soon
        Args:
            coords: (row, column) with 0-based indexing
        Returns:
            Boolean array where True represents cells in same box to cell given
        """
        board = np.full((9, 9), False, dtype=bool)
        board[
            3 * (coords[0] // 3) : 3 * (coords[0] // 3) + 3,
            3 * (coords[1] // 3) : 3 * (coords[1] // 3) + 3,
        ] = True  # Box
        return board

    @staticmethod
    def adjacent(coords: tuple[int, int]) -> npt.NDArray[np.bool]:
        """
        Will be deprecated soon
        Args:
            coords: (row, column) with 0-based indexing
        Returns:
            Boolean array where True represents cells adjacent to cell given
        """

        return (
            Board.adjacent_row(coords)
            | Board.adjacent_column(coords)
            | Board.adjacent_box(coords)
        )

    def all_normal(self) -> None:
        """
        Sets all normal hints to True
        """
        self._hints["normal"].add_hints(np.full((9, 9, 9), True, dtype=bool))

    def auto_normal(self) -> None:
        """
        Remove candidates from cells if they have a number adjacent to them
        """
        mask = np.full((9, 9, 9), False, dtype=bool)
        cells = self._cells.cells
        for cell in np.argwhere(cells != -1):
            num = cells[*cell]
            mask[num] = self.adjacent((cell[0], cell[1])) | mask[num]

            # Remove all hints if a cell is there
            mask[:, cell[0], cell[1]] = True

        self._hints["normal"].remove_hints(mask)


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
        cells = self._cells.cells
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
            self._cells._cells = solution


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
    board = Board(
        ".................................................................................",
    )
    start = time()
    i = 0
    for solution in board.solve():
        i += 1
        if i > 100_000:
            break
        # print(solution)
    print(time() - start)

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

# TODO: just make literally everything 0-based.
