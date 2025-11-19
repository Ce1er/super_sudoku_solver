from collections.abc import Generator

# from sudoku import Board
import sudoku
import numpy as np
import numpy.typing as npt
from human_solver import (
    MessagePart,
    Technique,
    Action,
    MessageCandidates,
    MessageCoord,
    MessageCoords,
    MessageNums,
    MessageNum,
    MessageText,
)
from itertools import combinations
import np_candidates as npc
import abc
from typing import Any
import logging
from human_solver import HumanSolver


class HumanTechniques(abc.ABC):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
        # board: HumanSolver
    ):
        # candidates = board.get_candidates()
        # clues = board.get_clues()
        # guesses = board.get_guesses()
        # cells = board.get_cells()
        cells = np.where(clues != -1, clues, guesses)

        if candidates.shape != (9, 9, 9):
            raise ValueError("Candidates has invalid shape")
        if candidates.dtype != np.bool:
            raise ValueError("Candidates has invalid dtype")

        if clues.shape != (9, 9):
            raise ValueError("Clues has invalid shape")
        if not np.issubdtype(clues.dtype, np.integer):
            raise ValueError("Clues has invalid dtype")
        if clues.dtype != np.int8:
            logging.warning(
                f"{__name__} instantiated with clues as dtype {clues.dtype}"
            )  # Not a real error just a small waste of memory

        if guesses.shape != (9, 9):
            raise ValueError("Guesses has invalid shape")
        if not np.issubdtype(guesses.dtype, np.signedinteger):
            raise ValueError("Guesses has invalid dtype")
        if guesses.dtype != np.int8:
            logging.warning(
                f"{__name__} instantiated with guesses as dtype {guesses.dtype}"
            )  # Not a real error just a small waste of memory

        if cells.shape != (9, 9):
            raise ValueError("Cells has invalid shape")
        if not np.issubdtype(cells.dtype, np.integer):
            raise ValueError("Cells has invalid dtype")
        if cells.dtype != np.int8:
            logging.warning(
                f"{__name__} instantiated with clues as dtype {cells.dtype}"
            )  # Not a real error just a small waste of memory

        self.candidates = candidates
        self.clues = clues
        self.guesses = guesses
        self.cells = cells

    @staticmethod
    @abc.abstractmethod
    def get_name() -> str: ...

    @abc.abstractmethod
    def find(self) -> Generator[Technique]: ...


def foo(coord: npt.NDArray[np.int8], num: npt.NDArray[np.int8]):
    new_cells = np.full((9, 9), -1, dtype=np.int8)
    new_cells[*coord] = num.flatten()
    return Action(new_cells)


class NakedSingles(HumanTechniques):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    @staticmethod
    def get_name():
        return "Naked Singles"

    @staticmethod
    def _generate_message(coord: npt.NDArray[np.int8], num: npt.NDArray[np.int8]):
        return [
            MessageCoord(coord, highlight=1),
            MessageText("is"),
            MessageNum(num),
            MessageText("because it is the only candidate for the cell."),
        ]

    @staticmethod
    def _generate_action(coord: npt.NDArray[np.int8], num: npt.NDArray[np.int8]):
        new_cells = np.full((9, 9), -1, dtype=np.int8)
        new_cells[*coord] = num[0][0]
        return Action(new_cells)

    def find(self):
        """
        Iterator of all Naked Singles based on self.candidates.
        Yields:
            Technique
        """
        naked_singles = np.add.reduce(self.candidates, axis=0, dtype=np.int8) == 1
        for coord in np.argwhere(naked_singles):
            row, column = coord
            num = np.argwhere(self.candidates[:, row, column])

            yield Technique(
                self.get_name(),
                NakedSingles._generate_message(coord, num),
                NakedSingles._generate_action(coord, num),
            )


class HiddenSingles(HumanTechniques):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    @staticmethod
    def get_name():
        return "Hidden Singles"

    @staticmethod
    def _generate_message(coord: npt.NDArray[np.int8], adjacency: str):
        """
        Args:
            coord: Shape (3,). [num, row, column]
            adjacency: box, row or column
        Returns:
            Message for hidden single at given coord
        """
        print(coord)
        print(coord.shape)
        if coord.shape != (3,):
            raise ValueError("Invalid coord shape")
        if not np.issubdtype(coord.dtype, np.integer):
            raise ValueError("Invalid coord dtype")

        if type(adjacency) is not str:
            raise ValueError("Invalid adjacency type")
        if adjacency not in ("row", "column", "box"):
            raise ValueError("Invalid adjacency value")

        return [
            MessageCoord(coord[1:], highlight=1),
            MessageText(" is "),
            MessageNum(coord[2]),
            MessageText(f" because there are no others in the {adjacency}."),
        ]

    @staticmethod
    def _generate_action(coord: npt.NDArray[np.int8]):
        """
        Args:
            coord: Shape (3,). [num, row, column]
        """
        if coord.shape != (3,):
            raise ValueError("Invalid coord shape")
        if not np.issubdtype(coord.dtype, np.integer):
            raise ValueError("Invalid coord dtype")

        new_cells = np.full((9, 9), -1, dtype=np.int8)
        new_cells[*coord[1:]] = coord[0]

        return Action(new_cells)

    def find(self) -> Generator[Technique]:
        """
        Search for Hidden Singles based on candidates.
        Yields:
            Technique
        """
        types = {
            sudoku.Board.adjacent_row: "row",
            sudoku.Board.adjacent_column: "column",
            sudoku.Board.adjacent_box: "box",
        }  # TODO: make this a class constant, and probably worth switching keys and values
        for coord in np.argwhere(self.candidates):
            num, row, column = coord
            for func, adjacency in types.items():
                adjacent = func((row, column)) & self.candidates[num]
                candidates_at_cell = self.candidates[:, row, column]

                # TODO: deprecate and replace with non_null_actions
                if not (
                    np.count_nonzero(adjacent) == 1
                    and len(np.argwhere(candidates_at_cell)) != 1
                ):
                    continue

                yield Technique(
                    "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
                    # TODO: check if comment above is actually right.
                    self._generate_message(coord, adjacency),
                    self._generate_action(coord),
                )


class NakedPairs(HumanTechniques):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    @staticmethod
    def get_name():
        return "Naked Pair"

    @staticmethod
    def _generate_message(pair, nums, remove_from):
        adjacencies = ""
        for item in remove_from:
            if len(adjacencies) == 0:
                pass
            else:
                adjacencies += ", "

            adjacencies += item

        return [
            MessageCoords(
                np.array([*pair]),
            ),
            MessageText(" are "),
            MessageNums(np.argwhere(nums)),
            MessageText(f" because they are adjacent by {adjacencies}."),
        ]

    @staticmethod
    def _generate_action(remove_from, cell, nums):
        pass
        # removed_candidates = np.full((9,9,9), False, dtype=np.bool)
        # for adjacency in remove_from:
        #     removed_candidates[nums] |= types[adjacency

    def find(self):
        """
        Search for Naked Pairs based on candidates.
        Yields:
            Technique
        """
        types = {
            "row": sudoku.Board.adjacent_row,
            "column": sudoku.Board.adjacent_column,
            "box": sudoku.Board.adjacent_box,
        }

        # Get cells where there are 2 candidates
        coords = np.argwhere(np.add.reduce(self.candidates, axis=0) == 2)
        for pair in combinations(coords, r=2):
            cell1 = pair[0]
            cell2 = pair[1]
            nums1 = self.candidates[:, *cell1]
            nums2 = self.candidates[:, *cell2]

            # If they don't have the same 2 candidates they aren't a pair
            if nums1.tolist() != nums2.tolist():
                continue

            nums = nums1

            # If they aren't adjacent they aren't a pair.
            if not sudoku.Board.adjacent((cell1[0], cell1[1]))[*cell2]:
                continue

            remove_from = []
            for adjacency, func in types.items():
                if func((cell1[0], cell1[1]))[*cell2]:
                    remove_from.append(adjacency)

            removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
            for adjacency in remove_from:
                removed_candidates[nums] |= types[adjacency]((cell1[0], cell1[1]))

            removed_candidates &= self.candidates

            if np.count_nonzero(removed_candidates) == 0:
                continue

            yield Technique(
                "Naked Pair",
                [
                    MessageCoords(np.array([*pair])),
                    MessageText("are"),
                    MessageNums(np.argwhere(nums)),
                    MessageText(
                        f" because they are adjacent by {", ".join(remove_from)}"
                    ),
                ],
                Action(remove_candidates=removed_candidates),
            )


class HiddenPairs(HumanTechniques):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    @staticmethod
    def get_name():
        return "Hidden Pairs"

    @staticmethod
    def _generate_message():
        pass

    @staticmethod
    def _generate_action():
        pass

    def find(self):
        """
        Search for Hidden Pairs based on candidates
        Yields:
            Technique
        """
        types = {
            "row": sudoku.Board.adjacent_row,
            "column": sudoku.Board.adjacent_column,
            "box": sudoku.Board.adjacent_box,
        }

        # Not strictly more than 2 because if one of them is hidden it counts as a hidden pair
        coords = np.argwhere(np.add.reduce(self.candidates, axis=0) >= 2)
        for pair in combinations(coords, r=2):
            cell1 = pair[0]
            cell2 = pair[1]
            nums1 = self.candidates[:, *cell1]
            nums2 = self.candidates[:, *cell2]

            common_nums_mask = nums1 & nums2
            common_nums = np.argwhere(common_nums_mask)

            # Pairs need at least 2 common candidates
            if len(common_nums) < 2:
                continue

            # this would make them naked
            if np.count_nonzero(nums1 | nums2) == 2:
                continue

            # Pairs must be adjacent
            if not sudoku.Board.adjacent((cell1[0], cell1[1]))[*cell2]:
                continue

            # Not super elegant or performant but the arrays are small enough that it really doesn't matter
            for num_pair in combinations(common_nums, r=2):
                num_pair = np.array([*num_pair])
                # print(num_pair)
                adjacent_by = []
                for adjacency, func in types.items():
                    # If they are adjacent by {adjacency} append adjacency to adjacent_by
                    if func((cell1[0], cell1[1]))[*cell2]:
                        adjacent_by.append(adjacency)

                temp = adjacent_by.copy()
                # 9x9 array where True means either (or both) nums are there
                # print(self.candidates[num_pair])
                other_occurences = np.logical_or.reduce(self.candidates[num_pair])
                # print(other_occurences)
                for adjacency in adjacent_by:
                    func = types[adjacency]
                    # print(func((cell1[0],cell1[1])))
                    if (
                        np.count_nonzero(func((cell1[0], cell1[1])) & other_occurences)
                        != 2
                    ):
                        temp.remove(adjacency)

                adjacent_by = temp

                if len(adjacent_by) == 0:
                    continue

                removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)

                cells = np.array([cell1, cell2])

                num_pair_mask = np.full((9), False, dtype=np.bool)

                num_pair_mask[num_pair] = True

                other_nums = np.argwhere(~num_pair_mask)

                # Remove any other candidates from the 2 cells that are part of the hidden pair
                removed_candidates[other_nums, cells[:, 0], cells[:, 1]] = True

                yield Technique(
                    "Hidden Pair",
                    [
                        MessageCoords(cells),
                        MessageText(" are the only cells that can be "),
                        MessageNums(num_pair),
                        MessageText(
                            " in their "
                            + ", ".join(adjacent_by)
                            + " so we can remove all other candidates from them"
                        ),
                    ],
                    Action(remove_candidates=removed_candidates),
                )


class LockedCandidates(HumanTechniques):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    @staticmethod
    def get_name():
        return "Locked Candidates"

    @staticmethod
    def _generate_message():
        pass

    @staticmethod
    def _generate_action():
        pass

    def find(self):
        """
        Search for Locked Candidates based on candidates
        Yields:
            Technique
        """
        seen = []
        types = {"column": npc.adjacent_column, "row": npc.adjacent_row}
        for coord in np.argwhere(self.candidates):
            num, row, column = coord
            for adjacency, func in types.items():
                # How many times candidate appears in adjacency
                adjacency_occurences = func(coord[1:]) & self.candidates[num]

                # How many of those times are in the current box
                adjacency_box_occurences = (
                    npc.adjacent_box(coord[1:]) & self.candidates[num]
                )

                adjacency_combined_occurences = (
                    adjacency_occurences & adjacency_box_occurences
                )

                # If all the occurences are in the box then it is a locked candidate
                if not (
                    np.count_nonzero(adjacency_occurences)
                    == np.count_nonzero(adjacency_combined_occurences)
                ):
                    continue
                # If there are no candidates to remove then there's no point in yielding the technique
                if np.count_nonzero(adjacency_box_occurences) == np.count_nonzero(
                    adjacency_combined_occurences
                ):
                    continue

                removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
                removed_candidates[num] = (
                    adjacency_box_occurences & ~adjacency_occurences
                )

                coords = np.argwhere(adjacency_combined_occurences)

                if coords.tobytes() in seen:
                    continue
                seen.append(coords.tobytes())

                yield Technique(
                    "Locked Candidate",
                    [
                        MessageCoords(coords),
                        MessageText(" are the only cells that can be "),
                        MessageNum(num),
                        MessageText(f" in their {adjacency} so we can remove "),
                        MessageNum(num),
                        MessageText(" from the other cells in their house."),
                    ],
                    Action(remove_candidates=removed_candidates),
                )


class PointingTuples(HumanTechniques):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    @staticmethod
    def get_name():
        return "Pointing Tuples"

    @staticmethod
    def _generate_message():
        pass

    @staticmethod
    def _generate_action():
        pass

    def find(self):
        """
        Search for Pointing Tuples
        Yields:
            Technique
        """
        seen = []
        types = {
            "column": sudoku.Board.adjacent_column,
            "row": sudoku.Board.adjacent_row,
        }
        for coord in np.argwhere(self.candidates):
            num, row, column = coord
            for adjacency, func in types.items():
                # TODO: these one-liners are getting way too long. Probably worth splitting up a bit to make things clearer.
                if (
                    x := np.count_nonzero(
                        sudoku.Board.adjacent_box((row, column)) & self.candidates[num]
                    )
                ) == np.count_nonzero(
                    self.candidates[num]
                    & sudoku.Board.adjacent_box((row, column))
                    & func((row, column))
                ) and np.count_nonzero(
                    self.candidates[num] & func((row, column))
                ) > x:

                    coords = np.argwhere(
                        sudoku.Board.adjacent_box((row, column))
                        & func((row, column))
                        & self.candidates[num]
                    )

                    if (result := (coords.tobytes(), num)) in seen:
                        continue
                    seen.append(result)

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
                            MessageText(" are the only cells that can be "),
                            MessageNum(num),
                            MessageText(
                                f" in their box so we can remove other options from their {adjacency}."
                            ),
                        ],
                        Action(remove_candidates=removed_candidates),
                    )


class Skyscrapers(HumanTechniques):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    @staticmethod
    def get_name():
        return "Skyscraper"

    @staticmethod
    def _generate_message():
        pass

    @staticmethod
    def _generate_action():
        pass

    def find(self):
        """
        Search for skyscrapers based on candidates
        Yields:
            Technique
        """
        types = {
            "column": sudoku.Board.adjacent_column,
            "row": sudoku.Board.adjacent_row,
        }

        for adjacency, func in types.items():
            for num in range(9):
                # Find rows or columns with 2 occurences of num. Will give 1d arr with ints representing index of row/column.
                if adjacency == "column":
                    rows = np.add.reduce(self.candidates[num], axis=0, dtype=np.int8)
                    potential = np.argwhere(rows == 2)
                elif adjacency == "row":
                    columns = np.add.reduce(self.candidates[num], axis=1, dtype=np.int8)
                    potential = np.argwhere(columns == 2)
                else:
                    assert False, "types has invalid key"

                if len(potential) < 2:
                    continue

                for pairing in combinations(potential, r=2):
                    # Check that one of the candidates in pairing[0] in same row/column to one of the candidates in pairing[0]
                    # The adjacency to check should be the opposite to adjacency
                    # So the check below is actually checking row adjacency not column
                    totals = None
                    if adjacency == "column":
                        totals = np.add.reduce(
                            self.candidates[num, :, pairing], axis=0, dtype=np.int8
                        )
                    elif adjacency == "row":
                        totals = np.add.reduce(
                            self.candidates[num, pairing, :], axis=0, dtype=np.int8
                        )

                    assert totals is not None

                    shared = totals == 2
                    non_shared = totals == 1

                    # Check that one pair of candidates share a row/column
                    if not (
                        np.count_nonzero(non_shared) == 2
                        and np.count_nonzero(shared) == 1
                    ):
                        continue

                    # Find cells that see both of the instances of num in the row/column in pairing which do not share a row/column
                    # Any cells that do see both can have num removed as a candidate
                    # These checks are actually checking the adjacency in the condition
                    if adjacency == "column":
                        rows = self.candidates[num, :, pairing] & ~shared
                        row1 = rows[0][0]
                        row2 = rows[1][0]
                        cell1_row = np.argwhere(row1)[0][0]
                        cell2_row = np.argwhere(row2)[0][0]

                        cell1_coord = np.array([cell1_row, pairing[0][0]])
                        cell2_coord = np.array([cell2_row, pairing[1][0]])

                        # Will be the same for the other 2 because they have to share a row
                        shared_row = self.candidates[num, :, pairing] & ~non_shared
                        shared_row = np.argwhere(shared_row[0][0])[0][0]

                        cell3_coord = np.array([shared_row, pairing[0][0]])
                        cell4_coord = np.array([shared_row, pairing[1][0]])

                        # cell3 and cell4 must be the only cells in the column
                        if np.count_nonzero(self.candidates[num, shared_row, :]) != 2:
                            continue

                    elif adjacency == "row":
                        cols = self.candidates[num, pairing, :] & ~shared
                        col1 = cols[0][0]
                        col2 = cols[1][0]
                        cell1_col = np.argwhere(col1)[0][0]
                        cell2_col = np.argwhere(col2)[0][0]

                        cell1_coord = np.array([pairing[0][0], cell1_col])
                        cell2_coord = np.array([pairing[1][0], cell2_col])

                        # Will be the same for the other 2 because they have to share a column
                        other_col = np.argwhere(
                            (self.candidates[num, pairing, :] & ~(non_shared))[0][0]
                        )[0][0]

                        cell3_coord = np.array([pairing[0][0], other_col])
                        cell4_coord = np.array([pairing[1][0], other_col])

                        # cell3 and cell4 must be the only cells in the column
                        if np.count_nonzero(self.candidates[num, :, other_col]) != 2:
                            continue
                    else:
                        assert False, "types has invalid key"

                    removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)

                    # Remove candidates that can see both cell1 and cell2
                    removed_candidates[num] = (
                        self.candidates[num]
                        & sudoku.Board.adjacent((cell1_coord[0], cell1_coord[1]))
                        & sudoku.Board.adjacent((cell2_coord[0], cell2_coord[1]))
                    )

                    # If nothing actually gets removed then the Technique is kinda useless
                    if np.count_nonzero(removed_candidates) == 0:
                        continue

                    other_adjacency = "row" if adjacency == "column" else "column"

                    yield Technique(
                        "Skyscraper",
                        [
                            MessageText("At least one of"),
                            MessageCoords(np.array([cell1_coord, cell2_coord])),
                            MessageText("must be"),
                            MessageNum(num),
                            MessageText(
                                f" because they are the only {num+1} in their {adjacency} except these "
                            ),
                            MessageCoords(np.array([cell3_coord, cell4_coord])),
                            MessageText(
                                f" which share a {other_adjacency}. That means"
                            ),
                            # MessageCandidates(removed_candidates),
                            MessageText(
                                f" which see both the cells that do not share a {other_adjacency} can't be {num+1}"
                            ),
                        ],
                        Action(remove_candidates=removed_candidates),
                    )


if __name__ == "__main__":
    print("going")
    x = NakedSingles(np.array([True]), np.array([1, 2]), np.array([1, 2]))

    for y in x.find():
        print(y)
