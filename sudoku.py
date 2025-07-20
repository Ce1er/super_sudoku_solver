from typing import Optional
import numpy as np
import numpy.typing as npt
import dlx_solver as dlx


class Cells:
    """
    Attributes:
        clues: the given numbers in a puzzle. e.g. 53..7....6..195... for first 2 rows of a puzzle.
        cells: the union of the given cells and guesses.
    """

    clues: npt.NDArray[np.int8]
    cells: npt.NDArray[np.int8]

    def __init__(self, clues: str):
        values = [-1 if clue == "." else int(clue) for clue in clues]
        self._clues = np.array(values, dtype=np.int8).reshape((9, 9))
        self._clues.flags.writeable = False

        self.cells = np.copy(self._clues)

    def add_cell(self, coordinate: tuple[int, int], value: int):
        self.cells[*coordinate] = value

    def get_cells(self) -> list[tuple[int, int, int]]:
        """
        Returns:
            list of (column, row, digit)
        """
        cells = []
        for coord in np.argwhere(self.cells < 10):
            coord = list(map(int, coord))
            cells.append((*coord, int(self.cells[coord[0]][coord[1]])))
        return cells


class Hints:
    """"""

    @staticmethod
    def hint_array(hints: list[dict[str, tuple[int, int]]]):
        np_hints = np.full((9, 9, 9), False, dtype=bool)
        for cell in hints:
            for value in cell["values"]:
                np_hints[*cell["coordinate"], value] = True
        return np_hints

    def __init__(self):
        """
        Args:
            hints: a list of dictionaries with the keys "coordinate" and "values"
                where the value of "coordinate" is a tuple containing the cartesian coordinate
                and "values" is a list of the values at that coordinate
        """
        self.hints = self.hint_array([])

    def add_hints(self, hints: list[dict[str, tuple[int, int]]]):
        for cell in hints:
            for value in cell["values"]:
                self.hints[*cell["coordinate"], value] = True

    def remove_hints(self, hints: list[dict[str, tuple[int, int]]]):
        for cell in hints:
            for value in cell["values"]:
                self.hints[*cell["coordinate"], value] = False

    def get_hints(self):
        return self.hints


class Board:
    def __init__(
        self,
        cells: str,
    ):  # TODO: work on args' types. Probably worth making them actually optional arguments instead of Optional[]
        # and take Hints as type instead of converting to it later.
        self.cells = Cells(cells)
        # TODO: allow clues and cells to be seperate
        self.hints = {
            "normal": Hints(),
            "highlighted": Hints(),
            "strikethrough": Hints(),
        }

    @staticmethod
    def _row_add(column, row, value):
        return [  # One value per constraint
            9 * row + column,  # Cell constraint
            81 + 9 * row + (value - 1),  # Row constraint
            162 + 9 * column + (value - 1),  # Column constraint
            243 + 9 * (3 * (row // 3) + (column // 3)) + (value - 1),  # Box constraint
        ]

    def create_matrix(self):
        """
        Labels are constraints
        Labels 0-80 one number per cell
        Labels 81-161 each digit once per row
        Labels 162-242 each digit once per column
        Labels 243-323 each digit once per box
        """
        rows = []

        # Number of rows = clues + 9 * (81-clues)
        for column, row, value in self.cells.get_cells():
            if value != -1:
                rows.append(self._row_add(column, row, value))
            else:
                for i in range(1, 10):
                    rows.append(self._row_add(column, row, i))

        # Only make labels for the ones referenced in rows
        labels = list(set(item for row in rows for item in row))
        return dlx.Matrix(labels, rows)

    @staticmethod
    def extract_from_matrix(solution):
        board: npt.NDArray = np.full((9, 9), -1, dtype=np.int8)
        for row in solution:
            row.sort()
            # Coordinates
            x = row[0] % 9
            y = row[0] // 9

            value = (row[1] - 81) % 9 + 1
            board[x][y] = value
        return board

    def solve(self, one_solution: bool = True):
        matrix = self.create_matrix()
        for solution in matrix.generate_solutions():
            yield self.extract_from_matrix(solution)
            if one_solution:
                break


#
#
# board = Board(
#     ".83..241.2.4..5....1..74.283..49.15...7.1...69..753.8.84....6..5...4..31136.2.5..",
#     {},
#     {},
#     {},
#     {},
#     {},
# )
# # Solution = "783962415294185763615374928328496157457218396961753284849531672572649831136827549"
# for solution in board.solve():
#     print(solution)
#
#
# board = Board(
#     ".5..8.......3...9.21..9...862.7..1....5.2......3.....6.....47..89..3...1..6......",
#     {},
#     {},
#     {},
#     {},
#     {},
# )
# for solution in board.solve():
#     print(solution)
#
board = Board(
    "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4..",
)
for solution in board.solve():
    print(solution)
