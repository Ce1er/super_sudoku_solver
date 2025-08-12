import numpy as np
import numpy.typing as npt
from sudoku import Board


class Technique:
    # Needs to contain data about highlighting
    # For hints and cells several types of highlighting will be available
    # Advanced example (Finned Jelyfish) to help decide how to implement
    # "These cells are a Jelyfish, if you don't include this cell that shares a house with part of it. That means that either the Jellyfish is valid, or this cell is 7 so this cell which contradicts both cannot be 7"
    # Technique("Finned Jellyfish", [np.NDarray, "are a Jellyfish, if you don't include" np.NDarray, "that shares a {adjacency} with part of it. That means that either the Jellyfish is valid, or this cell is {num} so", np.NDarray, "which contradicts both cannot be {num}")
    # Message takes list[str | npt.NDArray] numpy arrays are coordinates and are converted to human readable coords.
    # Highlighting could be good, cell groups mentioned in the message can have different colours. Maybe {adjacency} can be bold or smth.
    # Might be better if it is just a string with stuff like %1 for 1st group and give a dictionary {1: some numpy array of coords}

    @staticmethod
    def set_message(message: list[str | npt.NDArray[np.int8]]):
        new_message: str = ""
        for part in message:
            if isinstance(part, str):
                new_message += " " + part
            elif isinstance(part, np.ndarray):
                if part.size == 2:
                    # TODO: different coordinate formatting options
                    new_message += f" Cell ({part[0]+1}, {part[1]+1})"
                elif part.size == 1:
                    new_message += f" {int(part.reshape(1)[0])+1}"
                elif part.ndim == 3:
                    ...  # Candidates, all other parts are for cells
                else:
                    new_message += " Cells "
                    for coord in part:
                        new_message += f"({coord[0]+1}, {coord[1]+1})"
                # TODO: make message a bit better, sometimes spaces are there when they shouldn't be
        return new_message

    def __init__(self, technique, message):
        self.technique = technique
        self.message = self.set_message(message)
        print(self.message)

    def add_cell(self, *coords: npt.NDArray[np.int8]): ...

    def remove_candidates(self, candidates: npt.NDArray[np.int8]): ...


class Human_Solver:
    def __init__(self, board: Board) -> None:
        self.candidates: npt.NDArray[np.bool] = board.get_candidates()  # 9x9x9
        # dimension 1 = number

    @staticmethod
    def _pretty_coords(row, column):
        return f"({row+1}, {column+1})"

    def _naked_singles(self):
        for coord in np.argwhere(np.add.reduce(self.candidates, axis=0) == 1):
            row, column = coord
            num = np.argwhere(self.candidates[:, row, column])
            yield Technique(
                "Naked Single",
                [coord, "is", num, "because it is the only candidate for the cell."],
            )

    def _hidden_singles(self):
        types = {
            Board.adjacent_row: "row",
            Board.adjacent_column: "column",
            Board.adjacent_box: "box",
        }  # TODO: make this a class constant, and probably worth switching keys and values
        for coord in np.argwhere(self.candidates):
            num, row, column = coord
            for func, adjacency in types.items():
                if (
                    np.count_nonzero(func((row, column)) & self.candidates[num]) == 1
                ):  # TODO: also check for naked singles, honestly naked varieties seem like they tend to be different enough that it might make more sense to have in seperate functions. It would also make checking which technique is easiest easier as only the method used needs to be considered instead of the specifics of how the technique was applied.
                    print(
                        f"Cell ({row+1}, {column+1}) is {num+1} because there are no other {num+1}s in the {adjacency}"
                    )
                    x = Technique(
                        "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
                        f"Cell ({row+1}, {column+1}) is {num+1} because there are no other {num+1}s in the {adjacency}",
                    )
                    x.add_cell(coord)
                    yield x  # Maybe yield instead but this is prob best, only getting first one. Could make testing harder tho because if I reimplement it in a different way it could find a different single instead and which single to find really doesn't matter. Yielding could maybe give more flexibility with a hint system, allowing the user to see several examples.

    def _naked_pairs(self):
        types = {
            Board.adjacent_row: "row",
            Board.adjacent_column: "column",
            Board.adjacent_box: "box",
        }

        for coord in np.argwhere(np.add.reduce(self.candidates, axis=0) == 2):
            row, column = coord
            nums = np.argwhere(self.candidates[:, row, column])
            for func, adjacency in types.items():
                coords = np.argwhere(
                    np.logical_and.reduce(
                        func((row, column))
                        & self.candidates[nums]
                        & (np.add.reduce(self.candidates, axis=0) == 2),
                    ).reshape(9, 9)
                )

                nums = np.argwhere(self.candidates[:, coords[0][0], coords[0][1]])
                x = Technique(
                    "Naked Pair", "Cells {coords}, numbers {nums} along {adjacency}"
                )  # TODO: format coords
                yield x

    def _hidden_pairs(self):
        types = {
            Board.adjacent_row: "row",
            Board.adjacent_column: "column",
            Board.adjacent_box: "box",
        }
        for coord in np.argwhere(self.candidates):
            num, row, column = coord

            # Hidden pairs
            for func, adjacency in types.items():
                if np.count_nonzero(
                    func((row, column)) & self.candidates[num]
                ) == 2 and np.argwhere(
                    np.add.reduce(self.candidates, axis=0)
                ):  # TODO: some of these snippets will appear in lots of techniques, maybe make some helper functions
                    coords = np.argwhere(func((row, column)) & self.candidates[num])

                    # Num is always increasing so only check against higher nums
                    # There is probably a better way of doing this with some numpy tricks
                    for i in range(num + 1, 9):
                        if np.array_equal(
                            np.argwhere(func((row, column)) & self.candidates[i]),
                            coords,
                        ):
                            x = Technique(
                                "Hidden Pair",
                                f"Cells {coords[0]} and {coords[1]} are the only cells that can be {num} or {i} in their {adjacency}, so we can remove all other candidates from them.",
                            )  # TODO: make coords prettier and have something to check for other actions like removing those numbers in their box, so need to check if split or in same box
                            yield x

    def hint(self):
        types = [self._singles, self._pairs]
        # Maybe doing this async in some way could help. But because if only returns the easiest technique it might not be the easiest to do.
        # Could potentially start looking for all types at the same time and await them in order of easiest to hardest and return first non-null.
        # As long as I keep writing the techniques efficiently, using numpy as much as possible it shouldn't really matter if it is async or not but maybe it would with some of the more advanced techniques, like if I do 3d medusa chain analysis.
        for technique in types:
            x = technique()
            if x:
                yield x


if __name__ == "__main__":
    board = Board(
        ".18....7..7...19...6.85.12.6..7..3..7..51..8.8.4..97.5.47.98.5...26.5.3...6...24."
        # "................................................................................1"
        # "..............................................................................321"
    )

    board.auto_normal()

    human: Human_Solver = Human_Solver(board)

    human._naked_singles()

    # TODO: tests needed for all techniques. This is probably a higher priority than adding more techniques. Testing properly is tricky because there may be several valid ways to apply the technique and which one gets used really doesn't matter.
    # techniques are now yielded so tests should check all of them. Although there could maybe be some issues like if a hidden single was hidden single for box and column would that be 1 or 2 techniques.
