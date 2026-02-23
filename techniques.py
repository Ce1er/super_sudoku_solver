from collections.abc import Generator
import utils
import itertools
from os import remove

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
from typing import Any, Type, TypedDict, Self, Callable
import logging

# from human_solver import HumanSolver


class _HumanTechniques(abc.ABC):
    """
    Base class for all human techniques
    """
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
    def get_name() -> str:
        """
        Returns:
            Name of the technique
        """
        ...

    @staticmethod
    @abc.abstractmethod
    def _generate_message(technique: dict) -> list[MessagePart]:
        """
        Returns:
            The message that explains the technique
        """

        ...

    @staticmethod
    @abc.abstractmethod
    def _generate_action(technique: dict) -> Action:
        """
        Returns:
            The action for a technique
        """
        ...

    def _generate_techniques(self, technique: dict) -> Technique:
        """
        Returns:
            The technique which contains the name, message and action
        """
        name = self.get_name()
        message = self._generate_message(technique)
        action = self._generate_action(technique)
        return Technique(name, message, action)

    @abc.abstractmethod
    def _find(self) -> Generator[dict]: ...

    def _action_is_null(self, action: Action) -> bool:
        """
        To determine if an action will have any impact on the candidates
        Returns:
            True if action will have no effect. False if it will have an effect.
        """
        remove_candidates = action.get_candidates()
        add_cells = action.get_cells()

        if remove_candidates is not None:
            new_candidates = (~remove_candidates) & self.candidates
        else:
            new_candidates = np.copy(self.candidates)

        cells = np.copy(self.cells)
        if add_cells is not None:
            for coord in np.argwhere(add_cells != -1):
                cells[coord[0], coord[1]] = add_cells[*coord]

        return np.array_equal(self.candidates, new_candidates) and np.array_equal(
            self.cells, cells
        )

    def _non_null_actions(func: Callable[[Self], Generator[Technique]]) -> Callable[[Self], Generator[Technique]]:  # type: ignore[misc]
        """
        Decorator to filter Techniques to only include ones where the action has an effect on candidates and/or cells.
        Slightly simplifies technique detection as those functions are not responsible for checking if it has an effect or not.
        """

        # @wraps preserves dunder attributes of decorated functions
        # without it those attributes would refer to wrapper instead
        @wraps(func)
        def wrapper(self: Self) -> Generator[Technique]:
            for technique in func(self):
                if not self._action_is_null(technique.get_action()):
                    yield technique

        return wrapper

    def _non_duplicate_actions(func: Callable[[Self], Generator[Technique]]) -> Callable[[Self], Generator[Technique]]:  # type: ignore[misc]
        """
        Decorator to filter out duplicate techniques.
        Duplicates are techniques of the same type with an identical action.
        """

        @wraps(func)
        def wrapper(self: Self) -> Generator[Technique]:
            seen = []
            for technique in func(self):
                action = technique.get_action()
                name = technique.get_technique()

                hashed = hash((action, name))

                if hashed in seen:
                    continue

                seen.append(hashed)
                yield technique

        return wrapper

    @_non_duplicate_actions
    @_non_null_actions
    def find(self):
        for technique in self._find():
            yield self._generate_techniques(technique)


class NakedSingles(_HumanTechniques):
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
    def _generate_action(technique):
        coord = technique["coord"]
        num = technique["num"]

        new_cells = np.full((9, 9), -1, dtype=np.int8)
        new_cells[*coord] = num[0][0]
        return Action(new_cells)

    @staticmethod
    # def _generate_message(coord: npt.NDArray[np.int8], num: npt.NDArray[np.int8]):
    def _generate_message(technique):
        coord = technique["coord"]
        num = technique["num"]

        return [
            MessageCoord(coord, highlight=1),
            MessageText("is"),
            MessageNum(num),
            MessageText("because it is the only candidate for the cell."),
        ]

    def _find(self):
        """
        Iterator of all Naked Singles based on self.candidates.
        Yields:
            Technique
        """
        naked_singles = np.add.reduce(self.candidates, axis=0, dtype=np.int8) == 1
        for coord in np.argwhere(naked_singles):
            row, column = coord
            num = np.argwhere(self.candidates[:, row, column])

            yield {"coord": coord, "num": num}


class HiddenSingles(_HumanTechniques):
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
    # def _generate_message(coord: npt.NDArray[np.int8], adjacency: str):
    def _generate_message(technique: dict):
        """
        Args:
            coord: Shape (3,). [num, row, column]
            adjacency: box, row or column
        Returns:
            Message for hidden single at given coord
        """
        coord = technique["coord"]
        adjacency = technique["adjacency"]

        if coord.shape != (3,):
            raise ValueError("Invalid coord shape")
        if not np.issubdtype(coord.dtype, np.integer):
            raise ValueError("Invalid coord dtype")

        if type(adjacency) is not str:
            raise ValueError("Invalid adjacency type")
        if adjacency not in ("row", "column", "box"):
            raise ValueError("Invalid adjacency value")

        # print(coord)

        return [
            MessageCoord(coord[1:], highlight=1),
            MessageText(" is "),
            MessageNum(coord[2]),
            MessageText(f" because there are no others in the {adjacency}."),
        ]

    @staticmethod
    # def _generate_action(coord: npt.NDArray[np.int8]):
    def _generate_action(technique):
        """
        Args:
            coord: Shape (3,). [num, row, column]
        """
        coord = technique["coord"]

        if coord.shape != (3,):
            raise ValueError("Invalid coord shape")
        if not np.issubdtype(coord.dtype, np.integer):
            raise ValueError("Invalid coord dtype")

        new_cells = np.full((9, 9), -1, dtype=np.int8)
        new_cells[*coord[1:]] = coord[0]

        return Action(new_cells)

    def _find(self):
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

                yield {"coord": coord, "adjacency": adjacency}


class NakedPairs(_HumanTechniques):
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
    def remove_from(types, cell1, cell2):
        remove_from = []
        for adjacency, func in types.items():
            if func((cell1[0], cell1[1]))[*cell2]:
                remove_from.append(adjacency)
        return remove_from

    @staticmethod
    # def _generate_message(pair, nums, remove_from):
    def _generate_message(technique):
        pair = technique["pair"]
        nums = technique["nums"]
        cell1 = technique["cell1"]
        cell2 = technique["cell2"]
        types = technique["types"]

        remove_adjacencies = NakedPairs.remove_from(types, cell1, cell2)
        adjacencies = ""
        for item in remove_adjacencies:
            if len(adjacencies) == 0:
                pass
            else:
                adjacencies += ", "

            adjacencies += item

        return [
            MessageCoords(
                np.array([*pair]),highlight=1
            ),
            MessageText(" are "),
            MessageNums(np.argwhere(nums)),
            MessageText(f" because they are adjacent by {adjacencies}."),
        ]

    @staticmethod
    # def _generate_action(cell1, cell2, nums, types, candidates):
    def _generate_action(technique):
        cell1 = technique["cell1"]
        cell2 = technique["cell2"]
        nums = technique["nums"]
        types = technique["types"]
        candidates = technique["candidates"]

        remove_adjacencies = NakedPairs.remove_from(types, cell1, cell2)
        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
        for adjacency in remove_adjacencies:
            removed_candidates[nums] |= types[adjacency]((cell1[0], cell1[1]))

        removed_candidates &= candidates

        # FIXME: Pretty sure the problem is it is removing candidates from cell1 and cell2.
        # This should fix it but will break tests :(
        removed_candidates[:, cell1[0], cell1[1]] = False
        removed_candidates[:, cell2[0], cell2[1]] = False

        if np.count_nonzero(removed_candidates) == 0:
            return Action()

        return Action(remove_candidates=removed_candidates)

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

            yield {
                "pair": pair,
                "nums": nums,
                "cell1": cell1,
                "cell2": cell2,
                "types": types,
                "candidates": self.candidates,
            }


# TODO: Maybe make generic base class for pairs, triples and quadruples that these can inherit from. Since those techniques are similar.
class HiddenPairs(_HumanTechniques):
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
    def _generate_message(technique):
        cells = technique["cells"]
        num_pair = technique["num_pair"]
        adjacent_by = technique["adjacent_by"]

        return [
            MessageCoords(cells, highlight=1),
            MessageText(" are the only cells that can be "),
            MessageNums(num_pair),
            MessageText(
                " in their "
                + ", ".join(adjacent_by)
                + " so we can remove all other candidates from them"
            ),
        ]

    @staticmethod
    def _generate_action(technique):
        cells = technique["cells"]
        num_pair = technique["num_pair"]

        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)

        num_pair_mask = np.full((9), False, dtype=np.bool)

        num_pair_mask[num_pair] = True

        other_nums = np.argwhere(~num_pair_mask)

        # Remove any other candidates from the 2 cells that are part of the hidden pair
        removed_candidates[other_nums, cells[:, 0], cells[:, 1]] = True

        return Action(remove_candidates=removed_candidates)

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

                yield {
                    "cells": np.array([cell1, cell2]),
                    "num_pair": num_pair,
                    "adjacent_by": adjacent_by,
                }


class LockedCandidates(_HumanTechniques):
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
    def _generate_message(technique):
        coords = technique["coords"]
        num = technique["num"]
        adjacency = technique["adjacency"]

        return [
            MessageCoords(coords, highlight=1),
            MessageText(" are the only cells that can be "),
            MessageNum(num),
            MessageText(f" in their {adjacency} so we can remove "),
            MessageNum(num),
            MessageText(" from the other cells in their house."),
        ]

    @staticmethod
    def _generate_action(technique):
        num = technique["num"]
        adjacency_occurences = technique["adjacency_occurences"]
        adjacency_box_occurences = technique["adjacency_box_occurences"]

        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
        removed_candidates[num] = adjacency_box_occurences & ~adjacency_occurences

        return Action(remove_candidates=removed_candidates)

    def _find(self):
        """
        Search for Locked Candidates based on candidates
        Yields:
            Technique
        """
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

                yield {
                    "num": num,
                    "adjacency_occurences": adjacency_occurences,
                    "adjacency_box_occurences": adjacency_box_occurences,
                    "coords": np.argwhere(adjacency_combined_occurences),
                    "adjacency": adjacency,
                }

                # removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
                # removed_candidates[num] = (
                #     adjacency_box_occurences & ~adjacency_occurences
                # )
                #
                # coords = np.argwhere(adjacency_combined_occurences)
                #
                # if coords.tobytes() in seen:
                #     continue
                # seen.append(coords.tobytes())
                #
                # yield Technique(
                #     "Locked Candidate",
                #     [
                #         MessageCoords(coords),
                #         MessageText(" are the only cells that can be "),
                #         MessageNum(num),
                #         MessageText(f" in their {adjacency} so we can remove "),
                #         MessageNum(num),
                #         MessageText(" from the other cells in their house."),
                #     ],
                #     Action(remove_candidates=removed_candidates),
                # )


class _PointingTuples(_HumanTechniques):
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
            for coords in combinations(np.argwhere(self.candidates[num]), r=self.count):
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
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray,
        guesses: npt.NDArray[np.int8],
    ):
        _HumanTechniques.__init__(self, candidates, clues, guesses)
        _PointingTuples.__init__(self, candidates, clues, guesses, 2)

    @staticmethod
    def get_name():
        return "Pointing Pairs"

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
                self.get_name(),
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
# for coord in np.argwhere(self.candidates):
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
#             coords = np.argwhere(
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


class Skyscrapers(_HumanTechniques):
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
    def _generate_message(technique):
        cell1 = technique["cell1"]
        cell2 = technique["cell2"]
        cell3 = technique["cell3"]
        cell4 = technique["cell4"]
        num = technique["num"]
        adjacency = technique["adjacency"]
        other_adjacency = technique["other_adjacency"]

        return [
            MessageText("At least one of"),
            MessageCoords(np.array([cell1, cell2]),highlight=1),
            MessageText("must be"),
            MessageNum(num),
            MessageText(
                f" because they are the only {num+1} in their {adjacency} except these "
            ),
            MessageCoords(np.array([cell3, cell4]),highlight=1),
            MessageText(f" which share a {other_adjacency}. That means"),
            # MessageCandidates(removed_candidates),
            MessageText(
                f" which see both the cells that do not share a {other_adjacency} can't be {num+1}"
            ),
        ]

    @staticmethod
    def _generate_action(technique):
        num = technique["num"]
        cell1 = technique["cell1"]
        cell2 = technique["cell2"]
        candidates = technique["candidates"]

        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)

        # Remove candidates that can see both cell1 and cell2
        removed_candidates[num] = (
            candidates[num]
            & sudoku.Board.adjacent((cell1[0], cell1[1]))
            & sudoku.Board.adjacent((cell2[0], cell2[1]))
        )

        # If nothing actually gets removed then the Technique is kinda useless
        if np.count_nonzero(removed_candidates) == 0:
            return Action()

        return Action(remove_candidates=removed_candidates)

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

                        cell1 = np.array([cell1_row, pairing[0][0]])
                        cell2 = np.array([cell2_row, pairing[1][0]])

                        # Will be the same for the other 2 because they have to share a row
                        shared_row = self.candidates[num, :, pairing] & ~non_shared
                        shared_row = np.argwhere(shared_row[0][0])[0][0]

                        cell3 = np.array([shared_row, pairing[0][0]])
                        cell4 = np.array([shared_row, pairing[1][0]])

                        # cell3 and cell4 must be the only cells in the column
                        if np.count_nonzero(self.candidates[num, shared_row, :]) != 2:
                            continue

                    elif adjacency == "row":
                        cols = self.candidates[num, pairing, :] & ~shared
                        col1 = cols[0][0]
                        col2 = cols[1][0]
                        cell1_col = np.argwhere(col1)[0][0]
                        cell2_col = np.argwhere(col2)[0][0]

                        cell1 = np.array([pairing[0][0], cell1_col])
                        cell2 = np.array([pairing[1][0], cell2_col])

                        # Will be the same for the other 2 because they have to share a column
                        other_col = np.argwhere(
                            (self.candidates[num, pairing, :] & ~(non_shared))[0][0]
                        )[0][0]

                        cell3 = np.array([pairing[0][0], other_col])
                        cell4 = np.array([pairing[1][0], other_col])

                        # cell3 and cell4 must be the only cells in the column
                        if np.count_nonzero(self.candidates[num, :, other_col]) != 2:
                            continue
                    else:
                        assert False, "types has invalid key"

                    other_adjacency = "row" if adjacency == "column" else "column"

                    yield {
                        "cell1": cell1,
                        "cell2": cell2,
                        "cell3": cell3,
                        "cell4": cell4,
                        "num": num,
                        "adjacency": adjacency,
                        "other_adjacency": other_adjacency,
                        "candidates": self.candidates,
                    }


class XWing(_HumanTechniques):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    @staticmethod
    def get_name():
        return "X-Wing"

    @staticmethod
    def _generate_action(technique):
        pairing = np.array(technique["pairing"]).flatten()
        adjacency = technique["adjacency"]
        num = technique["num"]
        arr = technique["arr"]
        indices = np.array(np.argwhere(arr).flatten(), dtype=np.int8)

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
        indices = np.array(np.argwhere(arr).flatten(), dtype=np.int8)

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
                MessageCoords(coords,highlight=1),
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
                MessageCoords(coords,highlight=1),
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
                    potential = np.argwhere(rows == 2)
                elif adjacency == "row":
                    columns = np.add.reduce(self.candidates[num], axis=1, dtype=np.int8)
                    potential = np.argwhere(columns == 2)
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
