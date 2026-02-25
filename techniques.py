from collections.abc import Generator
import utils
import itertools
from os import remove
from dataclasses import dataclass

# from sudoku import Board
import sudoku
import copy
from functools import wraps
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
from typing import Any, SupportsInt, Type, TypedDict, Self, Callable, Literal
import logging
from types import Adjacency, Coord, Cells, CellCandidates, Candidates

# from human_solver import HumanSolver


class _TechniqueInstance(abc.ABC):
    """
    Base class for all human technique instances
    """

    NAME = "Unknown Technique"

    @property
    def name(self) -> str:
        return self.NAME

    @abc.abstractmethod
    def _generate_action(self) -> Action:
        pass

    @abc.abstractmethod
    def _generate_message(self) -> list[MessagePart]:
        pass

    @property
    def technique(self) -> Technique:
        return Technique(self.NAME, self._generate_message(), self._generate_action())


class _TechniqueFinder(abc.ABC):
    """
    Base class for all human technique finders
    """

    def __init__(
        self,
        candidates: Candidates,
        clues: Cells,
        guesses: Cells,
    ):
        cells = np.where(clues != -1, clues, guesses)

        if candidates.shape != (9, 9, 9):
            raise ValueError("Candidates has invalid shape")
        if candidates.dtype != np.bool:
            raise ValueError("Candidates has invalid dtype")

        if clues.shape != (9, 9):
            raise ValueError("Clues has invalid shape")
        if clues.dtype != np.int8:
            try:
                clues = clues.astype(np.int8, casting="same_value")
            except ValueError:
                raise ValueError("clues values could not be interpreted as np.int8")

        if guesses.shape != (9, 9):
            raise ValueError("Guesses has invalid shape")
        if guesses.dtype != np.int8:
            try:
                guesses = guesses.astype(np.int8, casting="same_value")
            except ValueError:
                raise ValueError("guesses values could not be interpreted as np.int8")

        if cells.shape != (9, 9):
            raise ValueError("Cells has invalid shape")
        if cells.dtype != np.int8:
            try:
                cells = cells.astype(np.int8, casting="same_value")
            except ValueError:
                raise ValueError("cells values could not be interpreted as np.int8")

        self._candidates = candidates
        self._clues = clues
        self._guesses = guesses
        self._cells = cells

        # They should never be mutated
        self._candidates.flags.writeable = False
        self._clues.flags.writeable = False
        self._guesses.flags.writeable = False
        self._cells.flags.writeable = False

    # @property
    # def candidates(self):
    #     return self._candidates
    #
    # @property
    # def clues(self):
    #     return self._clues
    #
    # @property
    # def guesses(self):
    #     return self._guesses
    #
    # @property
    # def cells(self):
    #     return self._cells
    #
    # @property
    # def name(self):
    #     return self.NAME

    @abc.abstractmethod
    def _find(self) -> Generator[_TechniqueInstance]: ...

    def _action_is_null(self, action: Action) -> bool:
        """
        To determine if an action will have any impact on the candidates
        Returns:
            True if action will have no effect. False if it will have an effect.
        """
        remove_candidates = action.candidates
        add_cells = action.cells

        if remove_candidates is not None:
            new_candidates = (~remove_candidates) & self._candidates
        else:
            new_candidates = np.copy(self._candidates)

        cells = np.copy(self._cells)
        if add_cells is not None:
            for coord in npc.argwhere(add_cells != -1):
                cells[coord[0], coord[1]] = add_cells[*coord]

        return np.array_equal(self._candidates, new_candidates) and np.array_equal(
            self._cells, cells
        )

    def _non_null_actions(func: Callable[[Self], Generator[Technique]]) -> Callable[[Self], Generator[Technique]]:  # type: ignore[misc]
        """
        Decorator to filter Techniques to only include ones where the action has an effect on candidates and/or cells.
        Slightly simplifies technique detection as those functions are not responsible for checking if it has an effect or not.
        """

        # @wraps preserves dunder attributes of decorated functions
        # without it those attributes would refer to wrapper() instead
        @wraps(func)
        def wrapper(self: Self) -> Generator[Technique]:
            for technique in func(self):
                if not self._action_is_null(technique.action):
                    yield technique

        return wrapper

    def _non_duplicate_actions(func: Callable[[Self], Generator[Technique]]) -> Callable[[Self], Generator[Technique]]:  # type: ignore[misc]
        """
        Decorator to filter out duplicate techniques.
        Duplicates are techniques of the same type with an identical action.
        """

        @wraps(func)
        def wrapper(self: Self) -> Generator[Technique]:
            seen = set()
            for technique in func(self):
                hashed = hash((technique.action, technique.technique))

                if hashed in seen:
                    continue

                seen.add(hashed)
                yield technique

        return wrapper

    @_non_duplicate_actions
    @_non_null_actions
    def find(self):
        for technique_instance in self._find():
            yield technique_instance.technique


class _NakedSinglesInstance(_TechniqueInstance):
    NAME = "Naked Singles"

    def __init__(self, coord: Coord, num: SupportsInt):
        self._coord = coord
        self._num = num

    def _generate_action(self):
        new_cells = np.full((9, 9), -1, dtype=np.int8)
        new_cells[*self._coord] = self._num
        return Action(new_cells)

    def _generate_message(self):
        return [
            MessageCoord(self._coord, highlight=1),
            MessageText("is"),
            MessageNum(self._num),
            MessageText("because it is the only candidate for the cell."),
        ]


class NakedSingles(_TechniqueFinder):
    def __init__(
        self,
        candidates,
        clues,
        guesses,
    ):
        super().__init__(candidates, clues, guesses)

    def _find(self):
        """
        Iterator of all Naked Singles based on self.candidates.
        Yields:
            Technique
        """
        naked_singles: Cells = (
            np.add.reduce(self._candidates, axis=0, dtype=np.int8) == 1
        )
        for coord in npc.argwhere(naked_singles).astype(np.int8, casting="same_value"):
            row, column = coord
            num = npc.argwhere(self._candidates[:, row, column]).flatten()[0]

            yield _NakedSinglesInstance(coord, num)


class _HiddenSinglesInstance(_TechniqueInstance):
    NAME = "Hidden Singles"

    def __init__(self, coord: npt.NDArray[np.int8], adjacency: Adjacency):
        self._coord = coord
        self._adjacency = adjacency

    def _generate_message(self):
        """
        Args:
            coord: Shape (3,). [num, row, column]
            adjacency: box, row or column
        Returns:
            Message for hidden single at given coord
        """
        if self._coord.shape != (3,):
            raise ValueError("Invalid coord shape")
        if not np.issubdtype(self._coord.dtype, np.integer):
            raise ValueError("Invalid coord dtype")

        if type(self._adjacency) is not str:
            raise ValueError("Invalid adjacency type")
        if self._adjacency not in ("row", "column", "box"):
            raise ValueError("Invalid adjacency value")

        # print(coord)

        return [
            MessageCoord(self._coord[1:], highlight=1),
            MessageText(" is "),
            MessageNum(self._coord[2]),
            MessageText(f" because there are no others in the {self._adjacency}."),
        ]

    def _generate_action(self):
        """
        Args:
            coord: Shape (3,). [num, row, column]
        """
        if self._coord.shape != (3,):
            raise ValueError("Invalid coord shape")
        if not np.issubdtype(self._coord.dtype, np.integer):
            raise ValueError("Invalid coord dtype")

        new_cells = np.full((9, 9), -1, dtype=np.int8)
        new_cells[*self._coord[1:]] = self._coord[0]

        return Action(new_cells)


class HiddenSingles(_TechniqueFinder):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    def _find(self):
        """
        Search for Hidden Singles based on candidates.
        Yields:
            Technique
        """
        types: dict[Callable, Adjacency] = {
            sudoku.Board.adjacent_row: "row",
            sudoku.Board.adjacent_column: "column",
            sudoku.Board.adjacent_box: "box",
        }  # TODO: make this a class constant, and probably worth switching keys and values
        for coord in npc.argwhere(self._candidates):
            num, row, column = coord
            for func, adjacency in types.items():
                adjacent = func((row, column)) & self._candidates[num]
                candidates_at_cell: CellCandidates = self._candidates[:, row, column]

                # TODO: deprecate and replace with non_null_actions
                if not (
                    np.count_nonzero(adjacent) == 1
                    and len(npc.argwhere(candidates_at_cell)) != 1
                ):
                    continue

                yield _HiddenSinglesInstance(coord, adjacency)


class _NakedPairsInstance(_TechniqueInstance):
    NAME = "Naked Pairs"

    def __init__(self, pair, nums, cell1, cell2, types, candidates):
        self._pair = pair
        self._nums = nums
        self._cell1 = cell1
        self._cell2 = cell2
        self._types = types
        self._candidates = candidates

    @property
    def _remove_from(self):
        remove_from = []
        for adjacency, func in self._types.items():
            if func((self._cell1[0], self._cell1[1]))[*self._cell2]:
                remove_from.append(adjacency)
        return remove_from

    def _generate_message(self):
        remove_adjacencies = self._remove_from
        adjacencies = ""
        for item in remove_adjacencies:
            if len(adjacencies) == 0:
                pass
            else:
                adjacencies += ", "

            adjacencies += item

        return [
            MessageCoords(np.array([*self._pair]), highlight=1),
            MessageText(" are "),
            MessageNums(npc.argwhere(self._nums)),
            MessageText(f" because they are adjacent by {adjacencies}."),
        ]

    def _generate_action(self):
        remove_adjacencies = self._remove_from
        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
        for adjacency in remove_adjacencies:
            removed_candidates[self._nums] |= self._types[adjacency](
                (self._cell1[0], self._cell1[1])
            )

        removed_candidates &= self._candidates

        # FIXME: Pretty sure the problem is it is removing candidates from cell1 and cell2.
        # This should fix it but will break tests :(
        removed_candidates[:, self._cell1[0], self._cell1[1]] = False
        removed_candidates[:, self._cell2[0], self._cell2[1]] = False

        if np.count_nonzero(removed_candidates) == 0:
            return Action()

        return Action(remove_candidates=removed_candidates)


class NakedPairs(_TechniqueFinder):
    NAME = "Naked Pairs"

    def __init__(
        self,
        candidates,
        clues,
        guesses,
    ):
        super().__init__(candidates, clues, guesses)

    def _find(self):
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
        coords = npc.argwhere(np.add.reduce(self._candidates, axis=0) == 2)
        for pair in combinations(coords, r=2):
            cell1 = pair[0]
            cell2 = pair[1]
            nums1 = self._candidates[:, *cell1]
            nums2 = self._candidates[:, *cell2]

            # If they don't have the same 2 candidates they aren't a pair
            if nums1.tolist() != nums2.tolist():
                continue

            nums = nums1

            # If they aren't adjacent they aren't a pair.
            if not sudoku.Board.adjacent((cell1[0], cell1[1]))[*cell2]:
                continue

            yield _NakedPairsInstance(
                pair,
                nums,
                cell1,
                cell2,
                types,
                self._candidates,
            )


class _HiddenPairsInstance(_TechniqueInstance):
    def __init__(self, cells, num_pair, adjacent_by):
        self._cells = cells
        self._num_pair = num_pair
        self._adjacent_by = adjacent_by

    def _generate_message(self):
        return [
            MessageCoords(self._cells, highlight=1),
            MessageText(" are the only cells that can be "),
            MessageNums(self._num_pair),
            MessageText(
                " in their "
                + ", ".join(self._adjacent_by)
                + " so we can remove all other candidates from them"
            ),
        ]

    def _generate_action(self):
        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)

        num_pair_mask = np.full((9), False, dtype=np.bool)

        num_pair_mask[self._num_pair] = True

        other_nums = npc.argwhere(~num_pair_mask)

        # Remove any other candidates from the 2 cells that are part of the hidden pair
        removed_candidates[other_nums, self._cells[:, 0], self._cells[:, 1]] = True

        return Action(remove_candidates=removed_candidates)


class HiddenPairs(_TechniqueFinder):
    NAME = "Hidden Pairs"

    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    def _find(self):
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
        coords = npc.argwhere(np.add.reduce(self._candidates, axis=0) >= 2)
        for pair in combinations(coords, r=2):
            cell1 = pair[0]
            cell2 = pair[1]
            nums1 = self._candidates[:, *cell1]
            nums2 = self._candidates[:, *cell2]

            common_nums_mask = nums1 & nums2
            common_nums = npc.argwhere(common_nums_mask)

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
                other_occurences = np.logical_or.reduce(self._candidates[num_pair])
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

                yield _HiddenPairsInstance(
                    np.array([cell1, cell2]),
                    num_pair,
                    adjacent_by,
                )


class _LockedCandidatesInstance(_TechniqueInstance):
    NAME = "Locked Candidates"

    def __init__(
        self, coords, num, adjacency, adjacency_occurences, adjacency_box_occurences
    ):
        self._coords = coords
        self._num = num
        self._adjacency = adjacency
        self._adjacency_occurences = adjacency_occurences
        self._adjacency_box_occurences = adjacency_box_occurences

    def _generate_message(self):
        return [
            MessageCoords(self._coords, highlight=1),
            MessageText(" are the only cells that can be "),
            MessageNum(self._num),
            MessageText(f" in their {self._adjacency} so we can remove "),
            MessageNum(self._num),
            MessageText(" from the other cells in their house."),
        ]

    def _generate_action(self):
        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
        removed_candidates[self._num] = (
            self._adjacency_box_occurences & ~self._adjacency_occurences
        )

        return Action(remove_candidates=removed_candidates)


class LockedCandidates(_TechniqueFinder):

    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    def _find(self):
        """
        Search for Locked Candidates based on candidates
        Yields:
            Technique
        """
        types = {"column": npc.adjacent_column, "row": npc.adjacent_row}
        for coord in npc.argwhere(self._candidates):
            num, row, column = coord
            for adjacency, func in types.items():
                # How many times candidate appears in adjacency
                adjacency_occurences = func(coord[1:]) & self._candidates[num]

                # How many of those times are in the current box
                adjacency_box_occurences = (
                    npc.adjacent_box(coord[1:]) & self._candidates[num]
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

                yield _LockedCandidatesInstance(
                    npc.argwhere(adjacency_combined_occurences),
                    num,
                    adjacency,
                    adjacency_occurences,
                    adjacency_box_occurences,
                )


class _PointingTuples(_TechniqueFinder):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray,
        guesses: npt.NDArray[np.int8],
        count: int,
    ):
        super().__init__(candidates, clues, guesses)

        if type(count) is not int:
            raise ValueError("Invalid type for count")
        elif count not in (2, 3):
            raise ValueError("Invalid tuple size. Only pairs and triples allowed.")
        self.count = count

    def partially_find(self):
        TYPES = {"column": npc.adjacent_column, "row": npc.adjacent_row}
        for num in range(9):
            for coords in combinations(
                npc.argwhere(self.candidates[num]), r=self.count
            ):
                coords = np.array([*coords])

                # Check all coords are in the same box
                if np.count_nonzero(npc.adjacent_box(coords)) != 9:
                    continue

                columns = np.count_nonzero(npc.adjacent_column(coords)) // 9
                rows = np.count_nonzero(npc.adjacent_row(coords)) // 9

                if np.count_nonzero(columns) == 1:
                    direction = "column"
                elif np.count_nonzero(rows) == 1:
                    direction = "row"
                else:
                    continue

                if (
                    np.count_nonzero(TYPES[direction](coords) & self.candidates[num])
                    <= self.count
                ):
                    continue

                yield {"coords": coords, "num": num, "direction": direction}


class PointingPairs(_PointingTuples):
    NAME = "Pointing Pairs"

    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray,
        guesses: npt.NDArray[np.int8],
    ):
        _TechniqueFinder.__init__(self, candidates, clues, guesses)
        _PointingTuples.__init__(self, candidates, clues, guesses, 2)

    @staticmethod
    def _generate_message(coords, num, direction):
        return [
            MessageCoords(coords, highlight=1),
            MessageText(" are the only cells that can be "),
            MessageNum(num),
            MessageText(
                f" in their box so we can remove other options from their {direction}."
            ),
        ]

    @staticmethod
    def _generate_action(coords, num, direction):
        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
        func = npc.adjacent_row if direction == "row" else npc.adjacent_column

        # TODO: np_candidates adjacency methods need more options. Like not including coords + and'ing coords instead of or
        removed_candidates[num, :, :] |= func(coords)
        for coord in coords:
            removed_candidates[num, coord[0], coord[1]] = False
        return Action(remove_candidates=removed_candidates)

    def find(self):
        for pair in self.partially_find():
            coords = pair["coords"]
            num = pair["num"]
            direction = pair["direction"]
            yield Technique(
                self.name,
                self._generate_message(coords, num, direction),
                self._generate_action(coords, num, direction),
            )


# class PointingTuples(HumanTechniques):
#     def __init__(
#         self,
#         candidates: npt.NDArray[np.bool],
#         clues: npt.NDArray[np.int8],
#         guesses: npt.NDArray[np.int8],
#     ):
#         super().__init__(candidates, clues, guesses)
#
#     @staticmethod
#     def get_name():
#         return "Pointing Tuples"
#
#     @staticmethod
#     def _generate_message():
#         pass
#
#     @staticmethod
#     def _generate_action():
#         pass
#
#     def find(self):
#         """
#         Search for Pointing Tuples
#         Yields:
#             Technique
#         """

# seen = []
# types = {
#     "column": sudoku.Board.adjacent_column,
#     "row": sudoku.Board.adjacent_row,
# }
# for coord in npc.argwhere(self.candidates):
#     num, row, column = coord
#     for adjacency, func in types.items():
#         if (
#             x := np.count_nonzero(
#                 sudoku.Board.adjacent_box((row, column)) & self.candidates[num]
#             )
#         ) == np.count_nonzero(
#             self.candidates[num]
#             & sudoku.Board.adjacent_box((row, column))
#             & func((row, column))
#         ) and np.count_nonzero(
#             self.candidates[num] & func((row, column))
#         ) > x:
#
#             coords = npc.argwhere(
#                 sudoku.Board.adjacent_box((row, column))
#                 & func((row, column))
#                 & self.candidates[num]
#             )
#
#             if (result := (coords.tobytes(), num)) in seen:
#                 continue
#             seen.append(result)
#
#             removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
#             removed_candidates[num, :, :] |= func((row, column))
#             new = np.full((9), True, dtype=np.bool)
#             new[num] = False
#             for coord in coords:
#                 removed_candidates[*coord] = new
#
#             yield Technique(
#                 "Pointing Tuple",
#                 [
#                     MessageCoords(coords),
#                     MessageText(" are the only cells that can be "),
#                     MessageNum(num),
#                     MessageText(
#                         f" in their box so we can remove other options from their {adjacency}."
#                     ),
#                 ],
#                 Action(remove_candidates=removed_candidates),
#             )


class _SkyscraperInstance(_TechniqueInstance):
    NAME = "Skyscraper"

    def __init__(
        self, cell1, cell2, cell3, cell4, num, adjacency, other_adjacency, candidates
    ):
        self._cell1 = cell1
        self._cell2 = cell2
        self._cell3 = cell3
        self._cell4 = cell4
        self._num = num
        self._adjacency = adjacency
        self._other_adjacency = other_adjacency
        self._candidates = candidates

    def _generate_message(self):
        return [
            MessageText("At least one of"),
            MessageCoords(np.array([self._cell1, self._cell2]), highlight=1),
            MessageText("must be"),
            MessageNum(self._num),
            MessageText(
                f" because they are the only {self._num+1} in their {self._adjacency} except these "
            ),
            MessageCoords(np.array([self._cell3, self._cell4]), highlight=1),
            MessageText(f" which share a {self._other_adjacency}. That means"),
            # MessageCandidates(removed_candidates),
            MessageText(
                f" which see both the cells that do not share a {self._other_adjacency} can't be {self._num+1}"
            ),
        ]

    def _generate_action(self):
        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)

        # Remove candidates that can see both cell1 and cell2
        removed_candidates[self._num] = (
            self._candidates[self._num]
            & sudoku.Board.adjacent((self._cell1[0], self._cell1[1]))
            & sudoku.Board.adjacent((self._cell2[0], self._cell2[1]))
        )

        # If nothing actually gets removed then the Technique is kinda useless
        if np.count_nonzero(removed_candidates) == 0:
            return Action()

        return Action(remove_candidates=removed_candidates)


class Skyscrapers(_TechniqueFinder):
    NAME = "Skyscraper"

    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    def _find(self):
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
                    rows = np.add.reduce(self._candidates[num], axis=0, dtype=np.int8)
                    potential = npc.argwhere(rows == 2)
                elif adjacency == "row":
                    columns = np.add.reduce(
                        self._candidates[num], axis=1, dtype=np.int8
                    )
                    potential = npc.argwhere(columns == 2)
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
                            self._candidates[num, :, pairing], axis=0, dtype=np.int8
                        )
                    elif adjacency == "row":
                        totals = np.add.reduce(
                            self._candidates[num, pairing, :], axis=0, dtype=np.int8
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
                        rows = self._candidates[num, :, pairing] & ~shared
                        row1 = rows[0][0]
                        row2 = rows[1][0]
                        cell1_row = npc.argwhere(row1)[0][0]
                        cell2_row = npc.argwhere(row2)[0][0]

                        cell1 = np.array([cell1_row, pairing[0][0]])
                        cell2 = np.array([cell2_row, pairing[1][0]])

                        # Will be the same for the other 2 because they have to share a row
                        shared_row = self._candidates[num, :, pairing] & ~non_shared
                        shared_row = npc.argwhere(shared_row[0][0])[0][0]

                        cell3 = np.array([shared_row, pairing[0][0]])
                        cell4 = np.array([shared_row, pairing[1][0]])

                        # cell3 and cell4 must be the only cells in the column
                        if np.count_nonzero(self._candidates[num, shared_row, :]) != 2:
                            continue

                    elif adjacency == "row":
                        cols = self._candidates[num, pairing, :] & ~shared
                        col1 = cols[0][0]
                        col2 = cols[1][0]
                        cell1_col = npc.argwhere(col1)[0][0]
                        cell2_col = npc.argwhere(col2)[0][0]

                        cell1 = np.array([pairing[0][0], cell1_col])
                        cell2 = np.array([pairing[1][0], cell2_col])

                        # Will be the same for the other 2 because they have to share a column
                        other_col = npc.argwhere(
                            (self._candidates[num, pairing, :] & ~(non_shared))[0][0]
                        )[0][0]

                        cell3 = np.array([pairing[0][0], other_col])
                        cell4 = np.array([pairing[1][0], other_col])

                        # cell3 and cell4 must be the only cells in the column
                        if np.count_nonzero(self._candidates[num, :, other_col]) != 2:
                            continue
                    else:
                        assert False, "types has invalid key"

                    other_adjacency = "row" if adjacency == "column" else "column"

                    yield _SkyscraperInstance(
                        cell1,
                        cell2,
                        cell3,
                        cell4,
                        num,
                        adjacency,
                        other_adjacency,
                        self._candidates,
                    )


class XWing(_TechniqueFinder):
    NAME = "X-Wing"

    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    @staticmethod
    def _generate_action(technique):
        pairing = np.array(technique["pairing"]).flatten()
        adjacency = technique["adjacency"]
        num = technique["num"]
        arr = technique["arr"]
        indices = np.array(npc.argwhere(arr).flatten(), dtype=np.int8)

        remove_candidates = np.full((9, 9, 9), False, dtype=np.bool)

        # Candidates will be removed in opposite direction to adjacency
        if adjacency == "column":
            remove_candidates[num, indices, :] = True

            coords = itertools.product(indices, pairing)
            for coord in coords:
                # Don't remove candidates for the cells that are part of the X-Wing
                remove_candidates[num, coord[0], coord[1]] = False

        elif adjacency == "row":
            remove_candidates[num, :, indices] = True

            coords = itertools.product(pairing, indices)
            for coord in coords:
                # Don't remove candidates for the cells that are part of the X-Wing
                remove_candidates[num, coord[0], coord[1]] = False

        return Action(remove_candidates=remove_candidates)

    @staticmethod
    def _generate_message(technique):
        # pairing = technique["pairing"]
        # adjacency = technique["adjacency"]
        # num = technique["num"]
        pairing = np.array(technique["pairing"]).flatten()
        adjacency = technique["adjacency"]
        num = technique["num"]
        arr = technique["arr"]
        indices = np.array(npc.argwhere(arr).flatten(), dtype=np.int8)

        if adjacency == "row":
            coords = np.array(
                list(
                    map(
                        lambda x: np.array(list(map(np.int8, x))),
                        itertools.product(pairing, indices),
                    )
                )
            )
            print(coords)
            message = [
                MessageCoords(coords, highlight=1),
                MessageText("are the only "),
                MessageNum(num),
                MessageText(f"s in their {adjacency} so we can remove "),
                MessageNum(num),
                MessageText("from all other cells in their columns."),
            ]
        elif adjacency == "column":
            coords = np.array(
                list(
                    map(
                        lambda x: np.array(list(map(np.int8, x))),
                        itertools.product(indices, pairing),
                    )
                )
            )
            print(coords)
            message = [
                MessageCoords(coords, highlight=1),
                MessageText("are the only "),
                MessageNum(num),
                MessageText(f"s in their {adjacency} so we can remove "),
                MessageNum(num),
                MessageText("from all other cells in their rows."),
            ]

        return message

    def _find(self):
        """
        Iterator of all X-Wings based on self.candidates.
        Yields:
            Technique
        """
        # only two possible cells for a value in each of two different rows,
        # and these candidates lie also in the same columns,
        # then all other candidates for this value in the columns can be eliminated.
        types = {
            "column": sudoku.Board.adjacent_column,
            "row": sudoku.Board.adjacent_row,
        }

        for adjacency, func in types.items():
            for num in range(9):
                # Find rows or columns with 2 occurences of num. Will give 1d arr with ints representing index of row/column.
                if adjacency == "column":
                    rows = np.add.reduce(self.candidates[num], axis=0, dtype=np.int8)
                    potential = npc.argwhere(rows == 2)
                elif adjacency == "row":
                    columns = np.add.reduce(self.candidates[num], axis=1, dtype=np.int8)
                    potential = npc.argwhere(columns == 2)
                else:
                    assert False, "types has invalid key"

                if len(potential) < 2:
                    continue

                for pairing in combinations(potential, r=2):
                    # print(adjacency, pairing)
                    if adjacency == "column":
                        arr = self.candidates[num, :, pairing]
                    if adjacency == "row":
                        arr = self.candidates[num, pairing, :]

                    if not np.array_equal(arr[0], arr[1]):
                        continue

                    # print(2, adjacency, pairing)

                    yield {
                        "adjacency": adjacency,
                        "pairing": pairing,
                        "num": num,
                        "arr": arr[0].flatten(),
                    }


TECHNIQUES = [
    NakedSingles,
    HiddenSingles,
    NakedPairs,
    HiddenPairs,
    LockedCandidates,
    Skyscrapers,
    XWing,
]

# TODO: consider finding more general techniques
# For example finding turbot fishes instead of skyscrapers
# Then skyscrapers can use that and check it is a special turbot fish that is also a skyscraper

# TODO:define clearly what the dictionaries used by the techniques should consist of
# probably worth making classes for them instead of using dictionaries


# TODO:
# Pointing Tuples
# Naked Triple
# X-Wing - I think it is done. Needs testing.
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
# 2-String Kite
# Empty Rectangle
# Color Chain
# Finned X-Wing
# Finned Swordfish
# Finned Jellyfish
