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


class Cage:
    """
    Attributes:
        total: the total of all numbers in cage
        cells: list of cartesian coordinates
    """

    sum: int
    mask: (
        npt.NDArray
    )  # Should be npt.NDArray[bool] but my typechecker doesn't like that

    def __init__(self, total: int, cells: list[tuple[int, int]]):
        self.sum = total
        mask: npt.NDArray = np.full((9, 9), False, dtype=bool)
        for cell in cells:
            mask[cell[0], cell[1]] = True
        self.mask = mask


class Hints:
    """"""

    @staticmethod
    def hint_array(hints):
        np_hints = np.full((9, 9, 9), False, dtype=bool)
        for cell in hints:
            for value in cell["values"]:
                np_hints[*cell["coordinate"], value] = True
        return np_hints

    def __init__(self, hints: Optional[list[dict[str, tuple[int, int] | list[int]]]]):
        """
        Args:
            hints: a list of dictionaries with the keys "coordinate" and "values"
                where the value of "coordinate" is a tuple containing the cartesian coordinate
                and "values" is a list of the values at that coordinate
        """
        self.hints = self.hint_array(hints)


class Board:
    def __init__(
        self,
        cells: str,
        totals: dict[int, int],
        cage_cells: Optional[dict[int, list[tuple[int, int]]]],
        normal: Optional[list[dict[str, tuple[int, int] | list[int]]]],
        strikethrough: Optional[list[dict[str, tuple[int, int] | list[int]]]],
        highlighted: Optional[list[dict[str, tuple[int, int] | list[int]]]],
    ):  # TODO: work on args' types. Probably worth making them actually optional arguments instead of Optional[]
        # and take Hints as type instead of converting to it later.
        self.cells = Cells(cells)
        # TODO: allow clues and cells to be seperate
        cages = []
        if cage_cells:
            for cage in totals.keys():
                cages.append(Cage(totals[cage], cage_cells[cage]))
        self.cages = cages

        self.normal = Hints(normal)
        self.strikethrough = Hints(strikethrough)
        self.highlighted = Hints(highlighted)

    @staticmethod
    def cage_combinations(total: int, cells: int) -> list[tuple[int]]:
        # leetcode 4sum but with all permutations
        """
        Yields:
            Tuples of all possible combinations of [1-9] that sum to total.
            Ignores the fact that cells in killer sudoku cages are typically adjacent.
            This means it will use up to 9 of the same number for a cage of size 9.
        """
        ...

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

        # Standard Sudoku
        # Number of rows = clues + 9 * (81-clues)
        for column, row, value in self.cells.get_cells():
            if value != -1:
                rows.append(self._row_add(column, row, value))
            else:
                # This is the bit to change for killer sudoku
                # In regular sudoku there are 9 different numbers that can go in each cell
                # The easiest way to optimise this would be to only add the numbers that would be valid for the cage
                # This would require no new rows or columns
                # Then check all solutions given at the end to see if they are valid
                # This could be further extended to use the fact that numbers in a box sum to 45 to work out which are valid
                # This would (hopefully) leave a fairly small number of potential solutions.

                # To make things more universal across varients it would be nice to represent possible values as a 9x9x9 binary matrix
                # Where True can represent possible values. Clues would have just one True value in the 3rd dimension.
                # This would make combining multiple varients together much easier as the union of the matrices could be taken.
                # Windoku, XV, Arrows, Anti-Knight, Thermometers, Renban, Argyle, Asterisk, Center Dot, Chain, DG could all make use of extra columns.
                # Some varients can be implemented in the exact same way with just UI changes. Some are basically the same thing but look different.
                # Geometry would be very well suited for extra columns as it is basically another constraint just like the ones for normal sudoku.
                # Diagonal sudoku as well.
                #
                # Kropki could be done to some extent with pre-processing but it wouldn't be that helpful
                # Even-odd could be done very well with pre-processing
                #
                # Most of these could be implemented like this:
                # Different colour regions (+ ideally different option for accessibility). Which usually either sum to smth or contain 1-9.
                # Anti-Knight would be much tricker but quite interesting. It would involve working out every possible knight move from every
                # cell and pairing those 2 cells together. At most this would be (8*81)/2=324 pairs. 324*9=2916 columns. But since knights
                # near the edge can't move as much it would probably be more like 4(2((2+3))) for edge, 4*2+6*4 for second to edge and 8*4*4
                # for the inside so 200 pairs. Which would mean 1800 columns, which is a lot but might be doable.
                #
                # Many of these varients could be combined together. Maybe even overlapping coloured regions.

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
    {},
    {},
    {},
    {},
    {},
)
for solution in board.solve():
    print(solution)
