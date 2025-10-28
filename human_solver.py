# import line_profiler
from collections.abc import Generator
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
        coord += 1
        self.text = "Cell ({}, {})".format(*coord)


class MessageCoords(MessagePart):
    def __init__(self, coords: npt.NDArray[np.intp], highlight=None) -> None:
        self.highlight = highlight
        tmp = "Cells"
        coords += 1
        for coord in coords:
            tmp += " ({}, {})".format(*coord.reshape(2))
        self.text = tmp


class MessageNum(MessagePart):
    def __init__(self, num: npt.NDArray[np.intp] | int, highlight=None) -> None:
        self.highlight = highlight

        if isinstance(num, np.ndarray):
            self.text = "number " + str(num.reshape(1)[0] + 1)
        else:
            self.text = "number " + str(num + 1)


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
    def __init__(
        self,
        add_cells: Optional[npt.NDArray[np.int8]] = None,
        remove_candidates: Optional[npt.NDArray[np.bool]] = None,
    ) -> None:
        self.add_cells = add_cells
        self.remove_candidates = remove_candidates

    # Board highlighting will be based off action if a full hint is used. And it will fully represent the candidates that can be removed / cells that can be added.
    def get_cells(self) -> Optional[npt.NDArray[np.int8]]:
        return self.add_cells

    def get_candidates(self) -> Optional[npt.NDArray[np.bool]]:
        return self.remove_candidates


class Technique:
    # Needs to contain data about highlighting
    # For hints and cells several types of highlighting will be available
    # Advanced example (Finned Jelyfish) to help decide how to implement
    # "These cells are a Jelyfish, if you don't include this cell that shares a house with part of it. That means that either the Jellyfish is valid, or this cell is 7 so this cell which contradicts both cannot be 7"
    # Message takes list[str | npt.NDArray] numpy arrays are coordinates and are converted to human readable coords.
    # Highlighting could be good, cell groups mentioned in the message can have different colours. Maybe {adjacency} can be bold or smth.
    # Might be better if it is just a string with stuff like %1 for 1st group and give a dictionary {1: some numpy array of coords}

    def __init__(self, technique: str, message: list[T], action: Action):
        self.technique = technique

        # TODO: highlights are ignored rewrite in a way that actually uses them.
        self.message = reduce(lambda prev, next: prev + next.get_text(), message, "")
        self.action = action

    def get_action(self) -> Action:
        return self.action

    def get_message(self) -> str:
        return self.message

    def get_technique(self) -> str:
        return self.technique


class Human_Solver:
    def __init__(self, board: Board) -> None:
        # TODO: maybe use board directly instead of copying from it. Or just stop using it entierly.
        # dimension 1 = number

        self.board: Board = board
        self.solution = None
        for solution in self.board.solve():
            if self.solution is not None:
                logging.warning("Multiple solutions")
                raise ValueError
            self.solution: npt.NDArray[np.int8] = solution

    @property
    def candidates(self):
        return self.board.get_candidates()

    @property
    def cells(self):
        return self.board.get_all_cells()

    def add_cells(self, cells: npt.NDArray[np.int8]):
        for row, col in np.argwhere(cells != -1):
            self.cells[row, col] = cells[row, col] + 1
            self.candidates[:, row, col] = False

    def remove_candidates(self, candidates: npt.NDArray[np.bool]):
        # self.candidates = (~candidates) & self.candidates
        self.board.remove_candidates(candidates)

    def get_candidates(self) -> npt.NDArray[np.bool]:
        return self.candidates

    # @line_profiler.profile
    def is_valid(self) -> bool:
        # for s in self.board.solve():
        #     if solution is not None:
        #         logging.warning("Multiple solutions")
        #         return False  # Multiple solutions
        #     solution = s

        # if solution is None:
        #     logging.warning("No solution")
        #     return False

        for row, col in np.argwhere(self.solution):
            if self.cells[row, col] not in (self.solution[row, col], -1):
                print(
                    f"{self._pretty_coords(row,col)} is {self.cells[row,col]+1} but should be {self.solution[row,col]+1}"
                )
                return False

            if self.cells[row, col] != -1 and (
                np.count_nonzero(self.candidates[:, row, col]) != 0
            ):
                print("Candidates in solved cell")
                # print(self.candidates[:, row, col])
                return False

        return True

    @staticmethod
    def _pretty_coords(row, column):
        return f"({row+1}, {column+1})"

    def auto_normal(self):
        # TODO: maybe make this a hint technique that explains why hints being removed
        self.board.auto_normal()

    def _naked_singles(self) -> Generator[Technique]:
        for coord in np.argwhere(
            (np.add.reduce(self.candidates, axis=0, dtype=np.int8)) == 1
        ):
            row, column = coord
            num = np.argwhere(self.candidates[:, row, column])  # .reshape(1)
            if num.size != 1:
                continue  # HACK: this should not be needed. The condition in the for loop should handle it but for some reason it is behaving weirdly.

            new_cells = np.full((9, 9), -1, dtype=np.int8)
            new_cells[row, column] = num[0][0]  # .reshape(1)

            yield Technique(
                "Naked Single",
                [
                    MessageCoord(coord, highlight=1),
                    MessageText("is"),
                    MessageNum(num),
                    MessageText("because it is the only candidate for the cell."),
                ],
                Action(new_cells),
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

                    new_cells = np.full((9, 9), -1, dtype=np.int8)
                    new_cells[row, column] = num

                    yield Technique(
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
                        Action(new_cells),
                    )

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

                removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
                for coord in coords:
                    removed_candidates[*coord] = True
                    removed_candidates[*coord, nums[0]] = False
                    removed_candidates[*coord, nums[1]] = False

                yield Technique(
                    "Naked Pair",
                    [
                        MessageCoords(coords, highlight=1),
                        MessageNums(nums),
                        MessageText(f"along {adjacency}"),
                    ],
                    Action(remove_candidates=removed_candidates),
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

                            removed_candidates = np.full(
                                (9, 9, 9), False, dtype=np.bool
                            )
                            for coord in coords:
                                removed_candidates[*coord] = True
                                removed_candidates[*coord, num] = False
                                removed_candidates[*coord, i] = False

                            yield Technique(
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
                                Action(remove_candidates=removed_candidates),
                            )

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

                    new_nums = np.full((9, 9, 9), -1, dtype=np.int8)
                    for coord in np.argwhere(x):
                        new_nums[*coord] = num
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
                        Action(new_nums),
                    )

    def _pointing_tuples(self):
        types = {"column": Board.adjacent_column, "row": Board.adjacent_row}
        for coord in np.argwhere(self.candidates):
            num, row, column = coord
            for adjacency, func in types.items():
                # TODO: these one-liners are getting way too long. Probably worth splitting up a bit to make things clearer.
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

                    coords = np.argwhere(
                        Board.adjacent_box((row, column))
                        & func((row, column))
                        & self.candidates[num]
                    )

                    removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
                    removed_candidates[num, :, :] |= func((row, column))
                    new = np.full((9), True, dtype=np.bool)
                    new[num] = False
                    for coord in coords:
                        removed_candidates[*coord] = new

                    yield Technique(
                        "Pointing Tuple",
                        [
                            MessageCoords(coords),
                            MessageText(
                                f"are the only cells that can be {num} in their box so we can remove other options from their {adjacency}."
                            ),
                        ],
                        Action(remove_candidates=removed_candidates),
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
            yield from technique()

    def apply_action(self, action: Action) -> None:
        if (x := action.get_cells()) is not None:
            self.add_cells(x)

        if (x := action.get_candidates()) is not None:
            self.remove_candidates(x)


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

    # TODO: check Action()'s thoroughly for all techniques.
