from typing import Optional, Generator
import numpy as np
import numpy.typing as npt
import dlx_solver as dlx


class Cells:
    """
    Attributes:
        clues: the given numbers in a puzzle. e.g. 53..7....6..195... for first 2 rows of a puzzle.
        cells: the union of the given cells and guesses.
    """

    _clues: npt.NDArray[np.int8]
    cells: npt.NDArray[np.int8]

    def __init__(self, clues: str) -> None:
        values = [-1 if clue == "." else int(clue) for clue in clues]
        self._clues = np.array(values, dtype=np.int8).reshape((9, 9))
        self._clues.flags.writeable = False

        self.cells = np.copy(self._clues)

    def add_cell(self, coordinate: tuple[int, int], value: int) -> None:
        self.cells[*coordinate] = value

    def get_cells(self, include_empty=False) -> list[tuple[int, int, int]]:
        """
        Returns:
            list of (column, row, digit)
            column, row are 0 based but digit is 1 based
        """
        cells = []
        for coord in np.argwhere(self.cells > (-2 if include_empty else 0)):
            coord = list(map(int, coord))
            cells.append((*coord, int(self.cells[coord[0], coord[1]])))
        return cells


class Hints:
    """
    Attributes:
        hints: 9x9x9 boolean array. First dimension is row, second is column, third is whether there is a hint there or not
            This means (x, y) 5 would be hints[y][x][4]
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
        self.hints: npt.NDArray[np.bool] = np.full((9, 9, 9), False, dtype=bool)
        self.rgba: tuple[int, int, int, int] = rgba
        self.candidate: bool = candidate
        self.strikethrough: Optional[tuple[int, int, int, int]] = strikethrough

    def is_candidate(self) -> bool:
        return self.candidate

    def add_hints(self, hints: npt.NDArray[np.bool]) -> None:
        self.hints = self.hints | hints

    def remove_hints(self, hints: npt.NDArray[np.bool]) -> None:
        self.hints = (~hints) & self.hints

    def get_hints(self) -> npt.NDArray[np.bool]:
        return self.hints


class Board:
    def __init__(
        self,
        cells: str,
    ) -> None:
        self.cells = Cells(cells)

        self.hints: dict[str, Hints] = {
            "normal": Hints((146, 153, 166, 255)),
            "highlighted": Hints((66, 197, 212, 255)),
            "strikethrough": Hints((146, 153, 166, 255), (214, 41, 32, 255), False),
        }

        AUTONORMAL = True  # TODO: move this to somewhere else. Idealing reading from a settings.* file.
        if AUTONORMAL:
            self.all_normal()

    def add_hint_type(
        self,
        name: str,
        rgba: tuple[int, int, int, int],
        strikethrough: Optional[tuple[int, int, int, int]],
    ) -> None:
        self.hints.update({name: Hints(rgba, strikethrough)})

    def remove_hint_type(self, name: str) -> None:
        self.hints.pop(name)

    @staticmethod
    def adjacent_row(coords: tuple[int, int]) -> npt.NDArray[np.bool]:
        """
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
        self.hints["normal"].add_hints(np.full((9, 9, 9), True, dtype=bool))

    def auto_normal(self) -> None:
        """
        Remove candidates from cells if they have a number adjacent to them
        """
        mask = np.full((9, 9, 9), False, dtype=bool)
        for cell in self.cells.get_cells():
            mask[cell[2] - 1] = self.adjacent((cell[0], cell[1])) | mask[cell[2] - 1]

            # Remove all hints if a cell is there
            mask[:, cell[0], cell[1]] = True

        self.hints["normal"].remove_hints(mask)

    def get_candidates(self) -> npt.NDArray[np.bool]:
        candidates = np.full((9, 9, 9), False, dtype=bool)

        for hint_type in self.hints.values():
            if hint_type.is_candidate():
                candidates = candidates | hint_type.get_hints()
        return candidates

    @staticmethod
    def _row_add(column: int, row: int, value: int) -> list[int]:
        return [  # One value per constraint
            9 * row + column,  # Cell constraint
            81 + 9 * row + (value - 1),  # Row constraint
            162 + 9 * column + (value - 1),  # Column constraint
            243 + 9 * (3 * (row // 3) + (column // 3)) + (value - 1),  # Box constraint
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
    def extract_from_matrix(solution: list[list[int]]) -> npt.NDArray[np.int8]:
        """
        Args:
            solution: a list of lists of labels from DLX matrix
        Returns:
            9x9 np.NDArray with full solution
        """
        board: npt.NDArray = np.full((9, 9), -1, dtype=np.int8)

        # Convert DLX matrix representation to 9x9 2D list[list[int]]
        for row in solution:
            row.sort()
            # Coordinates
            x = row[0] % 9
            y = row[0] // 9

            value = (row[1] - 81) % 9 + 1
            board[x][y] = value
        return board

    def solve(
        self, one_solution: bool = True
    ) -> Generator[npt.NDArray[np.int8], None, None]:
        matrix = self.create_matrix()
        for solution in matrix.generate_solutions():
            yield self.extract_from_matrix(solution)
            if one_solution:
                break


#
#
# board = Board(
#     ".83..241.2.4..5....1..74.283..49.15...7.1...69..753.8.84....6..5...4..31136.2.5..",
# )
# # Solution = "783962415294185763615374928328496157457218396961753284849531672572649831136827549"
# for solution in board.solve():
#     print(solution)
#
#
# board = Board(
#     ".5..8.......3...9.21..9...862.7..1....5.2......3.....6.....47..89..3...1..6......",
# )
# for solution in board.solve():
#     print(solution)
#
if __name__ == "__main__":
    board = Board(
        "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4..",
    )
    for solution in board.solve():
        print(solution)

    print("1, 2")
    print(board.adjacent((1, 2)))
    print("2, 2")
    print(board.adjacent((2, 2)))
    print("1, 1")
    print(board.adjacent((1, 1)))
    print("0, 0")
    print(board.adjacent((0, 0)))
    print("5, 8")
    print(board.adjacent((5, 8)))


# TODO: check I have x and y coordinates the right way round for all my methods
# and check all the +1s and -1s are correct
# It should always be row then column i.e. (y,x) as more common with sudoku rxcy
# Also worth thinking about 1/0 based indexing. Both are easier in different ways but 0-based is probably easiest.
# Think more about whether varients should be supported
