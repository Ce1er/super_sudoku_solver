from typing import Callable, Optional, Protocol, Type, TypeVar, Union
import numpy as np
import numpy.typing as npt
from sudoku import Board
import logging
from functools import reduce


# TODO: fix types. Mostly which specific np int type? Also consider non-numpy types being passed in such as int to MessageNum
class MessagePart(Protocol):
    text: str
    highlight: Optional[int]

    def get_text(self) -> str:
        return self.text

    def get_highlight(self) -> int | None:
        return self.highlight


# TODO: some sort of logic to work out when to capitalise words, where to put spaces etc.
class MessageText(MessagePart):
    def __init__(self, text, highlight=None) -> None:
        self.text = text
        self.highlight = highlight


class MessageCoord(MessagePart):
    def __init__(self, coord: npt.NDArray[np.intp], highlight=None) -> None:
        self.highlight = highlight
        coord.reshape(2)
        self.text = "Cell ({}, {})".format(*coord)


class MessageCoords(MessagePart):
    def __init__(self, coords: npt.NDArray[np.intp], highlight=None) -> None:
        self.highlight = highlight
        tmp = "Cells"
        for coord in coords:
            tmp += " ({}, {})".format(*coord.reshape(2))
        self.text = tmp


class MessageNum(MessagePart):
    def __init__(self, num: npt.NDArray[np.intp] | int, highlight=None) -> None:
        self.highlight = highlight

        if isinstance(num, np.ndarray):
            self.text = "number " + str(num.reshape(1)[0])
        else:
            self.text = "number " + str(num)


class MessageNums(MessagePart):
    def __init__(self, nums: npt.NDArray[np.intp], highlight=None) -> None:
        self.highlight = highlight
        tmp = "numbers"
        for num in nums:
            tmp += " " + str(num.reshape(1)[0])
        self.text = tmp


class MessageCandidates(MessagePart):
    def __init__(self, candidates: npt.NDArray[np.bool], highlight=None) -> None:
        self.highlight = highlight
        raise NotImplementedError


T = TypeVar("T", bound=MessagePart)


class Action:
    # TODO: actually use this
    def __init__(self, add_cells, remove_candidates) -> None: ...

    # Board highlighting will be based off action if a full hint is used. And it will fully represent the candidates that can be removed / cells that can be added.


class Technique:
    # Needs to contain data about highlighting
    # For hints and cells several types of highlighting will be available
    # Advanced example (Finned Jelyfish) to help decide how to implement
    # "These cells are a Jelyfish, if you don't include this cell that shares a house with part of it. That means that either the Jellyfish is valid, or this cell is 7 so this cell which contradicts both cannot be 7"
    # Technique("Finned Jellyfish", [np.NDarray, "are a Jellyfish, if you don't include" np.NDarray, "that shares a {adjacency} with part of it. That means that either the Jellyfish is valid, or this cell is {num} so", np.NDarray, "which contradicts both cannot be {num}")
    # Message takes list[str | npt.NDArray] numpy arrays are coordinates and are converted to human readable coords.
    # Highlighting could be good, cell groups mentioned in the message can have different colours. Maybe {adjacency} can be bold or smth.
    # Might be better if it is just a string with stuff like %1 for 1st group and give a dictionary {1: some numpy array of coords}

    def __init__(self, technique: str, message: list[T]):  # TODO: also take Action
        self.technique = technique

        # TODO: highlights are ignored rewrite in a way that actually uses them.
        self.message = reduce(lambda prev, next: prev + next.get_text(), message, "")

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
        for coord in np.argwhere(
            np.add.reduce(self.candidates, axis=0, dtype=np.int8) == 1
        ):
            row, column = coord
            num = np.argwhere(self.candidates[:, row, column])  # .reshape(1)
            yield Technique(
                "Naked Single",
                [
                    MessageCoord(coord, highlight=1),
                    MessageText("is"),
                    MessageNum(num),
                    MessageText("because it is the only candidate for the cell."),
                ],
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
                    and len(np.argwhere(self.candidates[:, row, column])) != 1
                ):

                    # TODO: also check for naked singles, honestly naked varieties seem like they tend to be different enough that it might make more sense to have in seperate functions. It would also make checking which technique is easiest easier as only the method used needs to be considered instead of the specifics of how the technique was applied.

                    x = Technique(
                        "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
                        # TODO: check if comment above is actually right.
                        [
                            MessageCoord(
                                np.array([row, column], dtype=np.int8), highlight=1
                            ),
                            MessageText("is"),
                            MessageNum(num),
                            MessageText(
                                f"because there are no others in the {adjacency}"
                            ),
                        ],
                        # f"Cell ({row+1}, {column+1}) is {num+1} because there are no other {num+1}s in the {adjacency}",
                    )
                    x.add_cell(coord)
                    #                     print(
                    #                         f"""
                    # Technique(
                    #                         "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
                    #                         f"Cell ({row+1}, {column+1}) is {num+1} because there are no other {num+1}s in the {adjacency}",
                    #                     ).add_cell({coord})
                    #
                    #                           """
                    #                     )
                    yield x  # Maybe yield instead but this is prob best, only getting first one. Could make testing harder tho because if I reimplement it in a different way it could find a different single instead and which single to find really doesn't matter. Yielding could maybe give more flexibility with a hint system, allowing the user to see several examples.

    def _naked_pairs(self):
        # TODO: it can give the same pair twice because it checks coordinates of both items. Fix this. Also a problem for hidden pairs. This isn't actually a problem, all the hints are still correct its just some are redundant. It would be quite nice for the hint to say stuff like it is a pair along the box and the column or whatever.
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
                if len(coords) != 2:
                    continue

                # Should be the same as checking the second coord. I think it is guarenteed but worth double checking.

                nums = np.argwhere(self.candidates[:, coords[0, 0], coords[0, 1]])

                yield Technique(
                    "Naked Pair",
                    [
                        MessageCoords(coords, highlight=1),
                        MessageNums(nums),
                        MessageText(f"along {adjacency}"),
                    ],
                )

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
                if (
                    np.count_nonzero(func((row, column)) & self.candidates[num]) == 2
                ):  # TODO: some of these snippets will appear in lots of techniques, maybe make some helper functions
                    coords = np.argwhere(func((row, column)) & self.candidates[num])
                    if len(coords) != 2:
                        continue

                    # Num is always increasing so only check against higher nums
                    # There is probably a better way of doing this with some numpy tricks
                    for i in range(num + 1, 9):
                        if np.array_equal(
                            np.argwhere(func((row, column)) & self.candidates[i]),
                            coords,
                        ):

                            x = Technique(
                                "Hidden Pair",
                                [
                                    MessageCoords(coords, highlight=1),
                                    MessageText("are the only cells that can be "),
                                    MessageNum(num),
                                    MessageText("or"),
                                    MessageNum(i),
                                    MessageText(
                                        f"in their {adjacency}, so we can remove all other candidates from them."
                                    ),
                                ],
                            )
                            # TODO: explanation incomplete and I don't like they way it uses way too many dictionaries. Make message input to Technique easier.
                            yield x

    def _locked_candidates(self):
        types = {"column": Board.adjacent_column, "row": Board.adjacent_row}
        for coord in np.argwhere(self.candidates):
            num, row, column = coord
            for adjacency, func in types.items():
                # TODO: passing in row, column in like this sucks. Make it take an np array instead.
                if np.count_nonzero(
                    func((row, column)) & self.candidates[num]
                ) == np.count_nonzero(
                    x := (
                        func((row, column))
                        & Board.adjacent_box((row, column))
                        & self.candidates[num]
                    )
                ) and np.count_nonzero(
                    x
                ) > np.count_nonzero(
                    Board.adjacent_box((row, column)) & self.candidates[num]
                ):
                    yield Technique(
                        "Locked Candidate",
                        [
                            MessageCoords(np.argwhere(x)),
                            MessageText("are the only cells that can be"),
                            MessageNum(num),
                            MessageText(f"In their {adjacency} so we can remove"),
                            MessageNum(num),
                            MessageText(
                                "from the other cells in their house"
                            ),  # TODO: make this MessageCandidates
                        ],
                    )

    def _pointing_tuples(self):
        types = {"column": Board.adjacent_column, "row": Board.adjacent_row}
        for coord in np.argwhere(self.candidates):
            num, row, column = coord
            for adjacency, func in types.items():
                if (
                    x := np.count_nonzero(
                        Board.adjacent_box((row, column)) & self.candidates[num]
                    )
                ) == np.count_nonzero(
                    self.candidates[num]
                    & Board.adjacent_box((row, column))
                    & func((row, column))
                ) and np.count_nonzero(
                    self.candidates[num] & func((row, column))
                ) > x:
                    # TODO: allow it to be several nums at same time. + avoid yielding effectively the same thing multiple times if possible
                    yield Technique(
                        "Pointing Tuple",
                        [
                            MessageCoords(
                                np.argwhere(
                                    Board.adjacent_box((row, column))
                                    & func((row, column))
                                    & self.candidates[num]
                                )
                            ),
                            MessageText(
                                f"are the only cells that can be {num} in their box so we can remove other options from their {adjacency}."
                            ),
                        ],
                    )

    def _naked_triples(self):
        pass

    # TODO:
    # Locked Candidates - untested but should work hopefully
    # Pointing Tuples - untested and probably needs a little tweaking
    # Naked Triple
    # X-Wing
    # Hidden Triple
    # Naked Quadruple
    # Y-Wing
    # Avoidable Rectangle
    # XYZ Wing
    # Hidden Quadruple
    # Unique Rectangle
    # Hidden Rectangle
    # Pointing Rectangle
    # Swordfish
    # Jellyfish
    # Skyscraper
    # 2-String Kite
    # Empty Rectangle
    # Color Chain
    # Finned X-Wing
    # Finned Swordfish
    # Finned Jellyfish

    def hint(self):
        types = [
            self._naked_singles,
            self._hidden_singles,
            self._naked_pairs,
            self._hidden_pairs,
            self._locked_candidates,
            self._pointing_tuples,
        ]
        # Maybe doing this async in some way could help. But because if only returns the easiest technique it might not be the easiest to do.
        # Could potentially start looking for all types at the same time and await them in order of easiest to hardest and return first non-null.
        # As long as I keep writing the techniques efficiently, using numpy as much as possible it shouldn't really matter if it is async or not but maybe it would with some of the more advanced techniques, like if I do 3d medusa chain analysis.
        for technique in types:
            for y in technique():
                if y:
                    yield y


if __name__ == "__main__":
    board = Board(
        ".18....7..7...19...6.85.12.6..7..3..7..51..8.8.4..97.5.47.98.5...26.5.3...6...24."
        # "................................................................................1"
        # "..............................................................................321"
    )

    board.auto_normal()

    human: Human_Solver = Human_Solver(board)

    for technique in human._hidden_singles():
        print("found")

    # TODO: tests needed for all techniques. This is probably a higher priority than adding more techniques. Testing properly is tricky because there may be several valid ways to apply the technique and which one gets used really doesn't matter.
    # techniques are now yielded so tests should check all of them. Although there could maybe be some issues like if a hidden single was hidden single for box and column would that be 1 or 2 techniques.
