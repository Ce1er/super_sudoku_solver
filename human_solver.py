# import line_profiler
from __future__ import annotations
import copy
from collections.abc import Generator
from typing import Callable, Optional, Protocol, Self, Type, TypeVar, Union
import numpy as np
import numpy.typing as npt
import sudoku
import logging
from functools import reduce, wraps
from itertools import combinations
import np_candidates as npc


# TODO: fix types. Mostly which specific np int type? Also consider non-numpy types being passed in such as int to MessageNum
class MessagePart(Protocol):
    """
    Base class for parts of message used by Technique
    This class should not be used directly
    """

    text: str
    highlight: Optional[int]

    def get_text(self) -> str:
        return self.text

    def get_highlight(self) -> int | None:
        return self.highlight


class MessageText(MessagePart):
    """
    Raw text with simple highlighting
    """

    def __init__(self, text: str, highlight: Optional[int] = None) -> None:
        """
        Args:
            text: raw text
            highlight: highlight group
        """
        self.text = text
        self.highlight = highlight


class MessageCoord(MessagePart):
    """
    For a single coordinate
    """

    def __init__(
        self, coord: npt.NDArray[np.signedinteger], highlight: Optional[int] = None
    ) -> None:
        """
        Args:
            coord: 0-based coordinate. size 2 and can be any ndim as long as it can be reshaped to (2,).
            highlight: highlight group
        """
        coord = np.copy(coord)
        self.highlight = highlight
        coord.reshape(2)
        coord += 1
        self.text = "Cell ({}, {})".format(*coord)


class MessageCoords(MessagePart):
    """
    For multiple coordinates
    """

    def __init__(
        self, coords: npt.NDArray[np.signedinteger], highlight: Optional[int] = None
    ) -> None:
        """
        Args:
            coords: 0 based coordinates. shape (..., 2). Num preceeding 2 can be anything. Anything preceeding that has to be 1.
            highlight: highlight group

        """
        coords = np.copy(coords)
        self.highlight = highlight
        tmp = "Cells"
        coords += 1
        for coord in coords:
            tmp += " ({}, {})".format(*coord.reshape(2))
        self.text = tmp


class MessageNum(MessagePart):
    """
    For a single number
    """

    def __init__(
        self, num: npt.NDArray[np.signedinteger] | int, highlight: Optional[int] = None
    ) -> None:
        """
        Args:
            num: np array size 1, any ndim. 0-based
            highlight: highlight group
        """
        self.highlight = highlight

        if isinstance(num, np.ndarray):
            self.text = "number " + str(num.reshape(1)[0] + 1)
        else:
            self.text = "number " + str(num + 1)


class MessageNums(MessagePart):
    """
    For several numbers
    """

    def __init__(
        self, nums: npt.NDArray[np.signedinteger], highlight: Optional[int] = None
    ) -> None:
        """
        Args:
            nums: np array shape (..., 1). Num preceeding 1 can be anything. Anything preceeding that is optional and has to be 1.
            highlight: highlight group
        """
        self.highlight = highlight
        tmp = "numbers"
        for num in nums:
            tmp += " " + str(num.reshape(1)[0] + 1)
        self.text = tmp


class MessageCandidates(MessagePart):
    """
    For candidates
    """

    def __init__(
        self, candidates: npt.NDArray[np.bool], highlight: Optional[int] = None
    ) -> None:
        """
        Args:
            candidates: np shape (9,9,9) (num, row, col) all 0-based
            highlight: highlight group
        """
        self.highlight = highlight
        raise NotImplementedError


T = TypeVar("T", bound=MessagePart)


class Action:
    """
    Represents the action that should be taken as a result of a Technique method
    """

    def __init__(
        self,
        add_cells: Optional[npt.NDArray[np.int8]] = None,
        remove_candidates: Optional[npt.NDArray[np.bool]] = None,
    ) -> None:
        """
        Args:
            add_cells: 9x9 0-based. -1 for no change.
            remove_candidates: 9x9x9 0-based. True means remove.
        """
        self.add_cells = add_cells
        self.remove_candidates = remove_candidates

    # Board highlighting will be based off action if a full hint is used. And it will fully represent the candidates that can be removed / cells that can be added.
    def get_cells(self) -> Optional[npt.NDArray[np.int8]]:
        return self.add_cells

    def get_candidates(self) -> Optional[npt.NDArray[np.bool]]:
        return self.remove_candidates


class Technique:
    """
    Represents a specific instance of a technique being used.
    Holds data about the technique and how to act on it.
    """

    # Needs to contain data about highlighting
    # For hints and cells several types of highlighting will be available
    # Advanced example (Finned Jelyfish) to help decide how to implement
    # "These cells are a Jelyfish, if you don't include this cell that shares a house with part of it. That means that either the Jellyfish is valid, or this cell is 7 so this cell which contradicts both cannot be 7"
    # Message takes list[str | npt.NDArray] numpy arrays are coordinates and are converted to human readable coords.
    # Highlighting could be good, cell groups mentioned in the message can have different colours. Maybe {adjacency} can be bold or smth.
    # Might be better if it is just a string with stuff like %1 for 1st group and give a dictionary {1: some numpy array of coords}

    def __init__(self, technique: str, message: list[T], action: Action):
        """
        Args:
            technique: Name of technique
            message: List of MessagePart subclasses. Message displayed to user.
            action: The action to perform. Which cells to add and which candidates to remove.
        """
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

#
# class HumanSolver:
#     """
#     Class holding methods for all human techniques
#     """
#
#     def __init__(self, board: sudoku.Board) -> None:
#         """
#         Args:
#             board: The board to start with
#         """
#         # TODO: maybe use board directly instead of copying from it. Or just stop using it entierly.
#         # dimension 1 = number
#
#         self.board: sudoku.Board = board
#         # self.solution: Optional[npt.NDArray[np.int8]] = None
#         # for solution in self.board.solve():
#         #     if self.solution is not None:
#         #         logging.warning("Multiple solutions")
#         #         raise ValueError
#         #     self.solution = solution
#
#     @property
#     def solution(self) -> npt.NDArray[np.int8]:
#         multiple_solutions = False
#         solution = None
#         for solution in self.board.solve():
#             if multiple_solutions:
#                 raise ValueError("Board has multiple solutions")
#             multiple_solutions = True
#
#         if solution is None:
#             raise ValueError("No solutions for board")
#         return solution
#
#     @property
#     def candidates(self) -> npt.NDArray[np.bool]:
#         """
#         9x9x9
#         """
#         return self.board.get_candidates()
#
#     @property
#     def cells(self) -> npt.NDArray[np.int8]:
#         """
#         9x9
#         """
#         return self.board.get_all_cells()
#
#     def add_cells(self, cells: npt.NDArray[np.int8]) -> None:
#         """
#         9x9 arr of cells to add
#         """
#         for row, col in np.argwhere(cells != -1):
#             # TODO: just keep it 0-based
#             self.cells[row, col] = cells[row, col]  # + 1
#             self.candidates[:, row, col] = False
#
#     def remove_candidates(self, candidates: npt.NDArray[np.bool]):
#         """
#         9x9x9 arr of candidates to remove
#         """
#         # self.candidates = (~candidates) & self.candidates
#         self.board.remove_candidates(candidates)
#
#     def get_candidates(self) -> npt.NDArray[np.bool]:
#         """
#         9x9x9 arr of candidates
#         """
#         return self.candidates
#
#     def get_cells(self) -> npt.NDArray[np.int8]:
#         """
#         9x9 arr of cells
#         """
#         return self.cells
#
#     def get_clues(self) -> npt.NDArray[np.int8]:
#         """
#         9x9 arr of clues
#         """
#         return self.board.get_clues()
#
#     def get_guesses(self) -> npt.NDArray[np.int8]:
#         """
#         9x9 arr of clues
#         """
#         return self.board.get_guesses()
#
#     def is_valid(self) -> bool:
#         """
#         Checks board is valid based on solution
#         """
#         for row, col in np.argwhere(self.solution):
#             if self.cells[row, col] not in (self.solution[row, col], -1):
#                 return False
#
#             if self.cells[row, col] != -1 and (
#                 np.count_nonzero(self.candidates[:, row, col]) != 0
#             ):
#                 print("Candidates in solved cell")
#                 # print(self.candidates[:, row, col])
#                 return False
#
#         return True
#
#     def auto_normal(self) -> None:
#         """
#         Removes normal hints if they have a candidate that is invalid due to being adjacent to a cell with that number as guess/clue.
#         """
#         # TODO: maybe make this a hint technique that explains why hints being removed
#         self.board.auto_normal()
#
#     def _action_is_null(self, action: Action) -> bool:
#         """
#         To determine if an action will have any impact on the candidates
#         Returns:
#             True if action will have no effect. False if it will have an effect.
#         """
#         board_copy = copy.deepcopy(self)
#         board_copy.apply_action(action)
#         diff_cands = (
#             self.get_candidates().tobytes() == board_copy.get_candidates().tobytes()
#         )
#         diff_cells = self.cells.tobytes() == board_copy.cells.tobytes()
#         return diff_cands and diff_cells
#
#     # Static method because the decorator (non_null_actions) does not take self.
#     # But it will still only ever be called over non-static methods.
#     @staticmethod
#     def _non_null_actions(func: Callable[[Self], Generator[Technique]]) -> Callable[[Self], Generator[Technique]]:  # type: ignore[misc]
#         """
#         Decorator to filter Techniques to only include ones where the action has an effect on candidates and/or cells.
#         Slightly simplifies technique detection as those functions are not responsible for checking if it has an effect or not.
#         """
#
#         # @wraps preserves dunder attributes of decorated functions
#         # without it those attributes would refer to wrapper instead
#         @wraps(func)
#         def wrapper(self: Self) -> Generator[Technique]:
#             for technique in func(self):
#                 if not self._action_is_null(technique.get_action()):
#                     yield technique
#
#         return wrapper
#
#     @_non_null_actions
#     def _naked_singles(self) -> Generator[Technique]:
#         """
#         Search for Naked Singles based on self.candidates.
#         Yields:
#             Technique
#         """
#         # print(self.candidates)
#         naked_singles = np.add.reduce(self.candidates, axis=0, dtype=np.int8) == 1
#         # print(naked_singles)
#         for coord in np.argwhere(naked_singles):
#             row, column = coord
#             num = np.argwhere(self.candidates[:, row, column])
#
#             new_cells = np.full((9, 9), -1, dtype=np.int8)
#             new_cells[row, column] = num[0][0]
#
#             # print(num)
#
#             yield Technique(
#                 "Naked Single",
#                 [
#                     MessageCoord(coord, highlight=1),
#                     MessageText("is"),
#                     MessageNum(num),
#                     MessageText("because it is the only candidate for the cell."),
#                 ],
#                 Action(new_cells),
#             )
#
#     @_non_null_actions
#     def _hidden_singles(self) -> Generator[Technique]:
#         """
#         Search for Hidden Singles based on self.candidates.
#         Yields:
#             Technique
#         """
#         types = {
#             sudoku.Board.adjacent_row: "row",
#             sudoku.Board.adjacent_column: "column",
#             sudoku.Board.adjacent_box: "box",
#         }  # TODO: make this a class constant, and probably worth switching keys and values
#         for coord in np.argwhere(self.candidates):
#             num, row, column = coord
#             for func, adjacency in types.items():
#                 adjacent = func((row, column)) & self.candidates[num]
#                 candidates_at_cell = self.candidates[:, row, column]
#                 if not (
#                     np.count_nonzero(adjacent) == 1
#                     and len(np.argwhere(candidates_at_cell)) != 1
#                 ):
#                     continue
#
#                 new_cells = np.full((9, 9), -1, dtype=np.int8)
#                 new_cells[row, column] = num
#
#                 yield Technique(
#                     "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#                     # TODO: check if comment above is actually right.
#                     [
#                         MessageCoord(
#                             np.array([row, column], dtype=np.int8), highlight=1
#                         ),
#                         MessageText("is"),
#                         MessageNum(num),
#                         MessageText(f"because there are no others in the {adjacency}"),
#                     ],
#                     Action(new_cells),
#                 )
#
#     @_non_null_actions
#     def _naked_pairs(self) -> Generator[Technique]:
#         """
#         Search for Naked Pairs based on self.candidates.
#         Yields:
#             Technique
#         """
#         types = {
#             "row": sudoku.Board.adjacent_row,
#             "column": sudoku.Board.adjacent_column,
#             "box": sudoku.Board.adjacent_box,
#         }
#
#         # Get cells where there are 2 candidates
#         coords = np.argwhere(np.add.reduce(self.candidates, axis=0) == 2)
#         for pair in combinations(coords, r=2):
#             cell1 = pair[0]
#             cell2 = pair[1]
#             nums1 = self.candidates[:, *cell1]
#             nums2 = self.candidates[:, *cell2]
#
#             # If they don't have the same 2 candidates they aren't a pair
#             if nums1.tolist() != nums2.tolist():
#                 continue
#
#             nums = nums1
#
#             # If they aren't adjacent they aren't a pair.
#             if not sudoku.Board.adjacent((cell1[0], cell1[1]))[*cell2]:
#                 continue
#
#             remove_from = []
#             for adjacency, func in types.items():
#                 if func((cell1[0], cell1[1]))[*cell2]:
#                     remove_from.append(adjacency)
#
#             removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
#             for adjacency in remove_from:
#                 removed_candidates[nums] |= types[adjacency]((cell1[0], cell1[1]))
#
#             removed_candidates &= self.candidates
#
#             if np.count_nonzero(removed_candidates) == 0:
#                 continue
#
#             yield Technique(
#                 "Naked Pair",
#                 [
#                     MessageCoords(np.array([*pair])),
#                     MessageText("are"),
#                     MessageNums(np.argwhere(nums)),
#                     MessageText(
#                         f" because they are adjacent by {", ".join(remove_from)}"
#                     ),
#                 ],
#                 Action(remove_candidates=removed_candidates),
#             )
#
#     @_non_null_actions
#     def _hidden_pairs(self) -> Generator[Technique]:
#         """
#         Search for Hidden Pairs based on self.candidates
#         Yields:
#             Technique
#         """
#         types = {
#             "row": sudoku.Board.adjacent_row,
#             "column": sudoku.Board.adjacent_column,
#             "box": sudoku.Board.adjacent_box,
#         }
#
#         # Not strictly more than 2 because if one of them is hidden it counts as a hidden pair
#         coords = np.argwhere(np.add.reduce(self.candidates, axis=0) >= 2)
#         for pair in combinations(coords, r=2):
#             cell1 = pair[0]
#             cell2 = pair[1]
#             nums1 = self.candidates[:, *cell1]
#             nums2 = self.candidates[:, *cell2]
#
#             common_nums_mask = nums1 & nums2
#             common_nums = np.argwhere(common_nums_mask)
#
#             # Pairs need at least 2 common candidates
#             if len(common_nums) < 2:
#                 continue
#
#             # this would make them naked
#             if np.count_nonzero(nums1 | nums2) == 2:
#                 continue
#
#             # Pairs must be adjacent
#             if not sudoku.Board.adjacent((cell1[0], cell1[1]))[*cell2]:
#                 continue
#
#             # Not super elegant or performant but the arrays are small enough that it really doesn't matter
#             for num_pair in combinations(common_nums, r=2):
#                 num_pair = np.array([*num_pair])
#                 # print(num_pair)
#                 adjacent_by = []
#                 for adjacency, func in types.items():
#                     # If they are adjacent by {adjacency} append adjacency to adjacent_by
#                     if func((cell1[0], cell1[1]))[*cell2]:
#                         adjacent_by.append(adjacency)
#
#                 temp = adjacent_by.copy()
#                 # 9x9 array where True means either (or both) nums are there
#                 # print(self.candidates[num_pair])
#                 other_occurences = np.logical_or.reduce(self.candidates[num_pair])
#                 # print(other_occurences)
#                 for adjacency in adjacent_by:
#                     func = types[adjacency]
#                     # print(func((cell1[0],cell1[1])))
#                     if (
#                         np.count_nonzero(func((cell1[0], cell1[1])) & other_occurences)
#                         != 2
#                     ):
#                         temp.remove(adjacency)
#
#                 adjacent_by = temp
#
#                 if len(adjacent_by) == 0:
#                     continue
#
#                 removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
#
#                 cells = np.array([cell1, cell2])
#
#                 num_pair_mask = np.full((9), False, dtype=np.bool)
#
#                 num_pair_mask[num_pair] = True
#
#                 other_nums = np.argwhere(~num_pair_mask)
#
#                 # Remove any other candidates from the 2 cells that are part of the hidden pair
#                 removed_candidates[other_nums, cells[:, 0], cells[:, 1]] = True
#
#                 yield Technique(
#                     "Hidden Pair",
#                     [
#                         MessageCoords(cells),
#                         MessageText(" are the only cells that can be "),
#                         MessageNums(num_pair),
#                         MessageText(
#                             " in their "
#                             + ", ".join(adjacent_by)
#                             + " so we can remove all other candidates from them"
#                         ),
#                     ],
#                     Action(remove_candidates=removed_candidates),
#                 )
#
#     @_non_null_actions
#     def _locked_candidates(self) -> Generator[Technique]:
#         """
#         Search for Locked Candidates based on self.candidates
#         Yields:
#             Technique
#         """
#         seen = []
#         types = {"column": npc.adjacent_column, "row": npc.adjacent_row}
#         for coord in np.argwhere(self.candidates):
#             num, row, column = coord
#             for adjacency, func in types.items():
#                 # How many times candidate appears in adjacency
#                 adjacency_occurences = func(coord[1:]) & self.candidates[num]
#
#                 # How many of those times are in the current box
#                 adjacency_box_occurences = (
#                     npc.adjacent_box(coord[1:]) & self.candidates[num]
#                 )
#
#                 adjacency_combined_occurences = (
#                     adjacency_occurences & adjacency_box_occurences
#                 )
#
#                 # If all the occurences are in the box then it is a locked candidate
#                 if not (
#                     np.count_nonzero(adjacency_occurences)
#                     == np.count_nonzero(adjacency_combined_occurences)
#                 ):
#                     continue
#                 # If there are no candidates to remove then there's no point in yielding the technique
#                 if np.count_nonzero(adjacency_box_occurences) == np.count_nonzero(
#                     adjacency_combined_occurences
#                 ):
#                     continue
#
#                 removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
#                 removed_candidates[num] = (
#                     adjacency_box_occurences & ~adjacency_occurences
#                 )
#
#                 coords = np.argwhere(adjacency_combined_occurences)
#
#                 if coords.tobytes() in seen:
#                     continue
#                 seen.append(coords.tobytes())
#
#                 yield Technique(
#                     "Locked Candidate",
#                     [
#                         MessageCoords(coords),
#                         MessageText(" are the only cells that can be "),
#                         MessageNum(num),
#                         MessageText(f" in their {adjacency} so we can remove "),
#                         MessageNum(num),
#                         MessageText(" from the other cells in their house."),
#                     ],
#                     Action(remove_candidates=removed_candidates),
#                 )
#
#     @_non_null_actions
#     def _pointing_tuples(self) -> Generator[Technique]:
#         """
#         Search for Pointing Tuples
#         Yields:
#             Technique
#         """
#         seen = []
#         types = {
#             "column": sudoku.Board.adjacent_column,
#             "row": sudoku.Board.adjacent_row,
#         }
#         for coord in np.argwhere(self.candidates):
#             num, row, column = coord
#             for adjacency, func in types.items():
#                 # TODO: these one-liners are getting way too long. Probably worth splitting up a bit to make things clearer.
#                 if (
#                     x := np.count_nonzero(
#                         sudoku.Board.adjacent_box((row, column)) & self.candidates[num]
#                     )
#                 ) == np.count_nonzero(
#                     self.candidates[num]
#                     & sudoku.Board.adjacent_box((row, column))
#                     & func((row, column))
#                 ) and np.count_nonzero(
#                     self.candidates[num] & func((row, column))
#                 ) > x:
#
#                     coords = np.argwhere(
#                         sudoku.Board.adjacent_box((row, column))
#                         & func((row, column))
#                         & self.candidates[num]
#                     )
#
#                     if (result := (coords.tobytes(), num)) in seen:
#                         continue
#                     seen.append(result)
#
#                     removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
#                     removed_candidates[num, :, :] |= func((row, column))
#                     new = np.full((9), True, dtype=np.bool)
#                     new[num] = False
#                     for coord in coords:
#                         removed_candidates[*coord] = new
#
#                     yield Technique(
#                         "Pointing Tuple",
#                         [
#                             MessageCoords(coords),
#                             MessageText(" are the only cells that can be "),
#                             MessageNum(num),
#                             MessageText(
#                                 f" in their box so we can remove other options from their {adjacency}."
#                             ),
#                         ],
#                         Action(remove_candidates=removed_candidates),
#                     )
#
#     @_non_null_actions
#     def _skyscraper(self) -> Generator[Technique]:
#         """
#         Search for skyscrapers based on self.candidates
#         Yields:
#             Technique
#         """
#         types = {
#             "column": sudoku.Board.adjacent_column,
#             "row": sudoku.Board.adjacent_row,
#         }
#
#         for adjacency, func in types.items():
#             for num in range(9):
#                 # Find rows or columns with 2 occurences of num. Will give 1d arr with ints representing index of row/column.
#                 if adjacency == "column":
#                     rows = np.add.reduce(self.candidates[num], axis=0, dtype=np.int8)
#                     potential = np.argwhere(rows == 2)
#                 elif adjacency == "row":
#                     columns = np.add.reduce(self.candidates[num], axis=1, dtype=np.int8)
#                     potential = np.argwhere(columns == 2)
#                 else:
#                     assert False, "types has invalid key"
#
#                 if len(potential) < 2:
#                     continue
#
#                 for pairing in combinations(potential, r=2):
#                     # Check that one of the candidates in pairing[0] in same row/column to one of the candidates in pairing[0]
#                     # The adjacency to check should be the opposite to adjacency
#                     # So the check below is actually checking row adjacency not column
#                     totals = None
#                     if adjacency == "column":
#                         totals = np.add.reduce(
#                             self.candidates[num, :, pairing], axis=0, dtype=np.int8
#                         )
#                     elif adjacency == "row":
#                         totals = np.add.reduce(
#                             self.candidates[num, pairing, :], axis=0, dtype=np.int8
#                         )
#
#                     assert totals is not None
#
#                     shared = totals == 2
#                     non_shared = totals == 1
#
#                     # Check that one pair of candidates share a row/column
#                     if not (
#                         np.count_nonzero(non_shared) == 2
#                         and np.count_nonzero(shared) == 1
#                     ):
#                         continue
#
#                     # Find cells that see both of the instances of num in the row/column in pairing which do not share a row/column
#                     # Any cells that do see both can have num removed as a candidate
#                     # These checks are actually checking the adjacency in the condition
#                     if adjacency == "column":
#                         rows = self.candidates[num, :, pairing] & ~shared
#                         row1 = rows[0][0]
#                         row2 = rows[1][0]
#                         cell1_row = np.argwhere(row1)[0][0]
#                         cell2_row = np.argwhere(row2)[0][0]
#
#                         cell1_coord = np.array([cell1_row, pairing[0][0]])
#                         cell2_coord = np.array([cell2_row, pairing[1][0]])
#
#                         # Will be the same for the other 2 because they have to share a row
#                         shared_row = self.candidates[num, :, pairing] & ~non_shared
#                         shared_row = np.argwhere(shared_row[0][0])[0][0]
#
#                         cell3_coord = np.array([shared_row, pairing[0][0]])
#                         cell4_coord = np.array([shared_row, pairing[1][0]])
#
#                         # cell3 and cell4 must be the only cells in the column
#                         if np.count_nonzero(self.candidates[num, shared_row, :]) != 2:
#                             continue
#
#                     elif adjacency == "row":
#                         cols = self.candidates[num, pairing, :] & ~shared
#                         col1 = cols[0][0]
#                         col2 = cols[1][0]
#                         cell1_col = np.argwhere(col1)[0][0]
#                         cell2_col = np.argwhere(col2)[0][0]
#
#                         cell1_coord = np.array([pairing[0][0], cell1_col])
#                         cell2_coord = np.array([pairing[1][0], cell2_col])
#
#                         # Will be the same for the other 2 because they have to share a column
#                         other_col = np.argwhere(
#                             (self.candidates[num, pairing, :] & ~(non_shared))[0][0]
#                         )[0][0]
#
#                         cell3_coord = np.array([pairing[0][0], other_col])
#                         cell4_coord = np.array([pairing[1][0], other_col])
#
#                         # cell3 and cell4 must be the only cells in the column
#                         if np.count_nonzero(self.candidates[num, :, other_col]) != 2:
#                             continue
#                     else:
#                         assert False, "types has invalid key"
#
#                     removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
#
#                     # Remove candidates that can see both cell1 and cell2
#                     removed_candidates[num] = (
#                         self.candidates[num]
#                         & sudoku.Board.adjacent((cell1_coord[0], cell1_coord[1]))
#                         & sudoku.Board.adjacent((cell2_coord[0], cell2_coord[1]))
#                     )
#
#                     # If nothing actually gets removed then the Technique is kinda useless
#                     if np.count_nonzero(removed_candidates) == 0:
#                         continue
#
#                     other_adjacency = "row" if adjacency == "column" else "column"
#
#                     yield Technique(
#                         "Skyscraper",
#                         [
#                             MessageText("At least one of"),
#                             MessageCoords(np.array([cell1_coord, cell2_coord])),
#                             MessageText("must be"),
#                             MessageNum(num),
#                             MessageText(
#                                 f" because they are the only {num+1} in their {adjacency} except these "
#                             ),
#                             MessageCoords(np.array([cell3_coord, cell4_coord])),
#                             MessageText(
#                                 f" which share a {other_adjacency}. That means"
#                             ),
#                             # MessageCandidates(removed_candidates),
#                             MessageText(
#                                 f" which see both the cells that do not share a {other_adjacency} can't be {num+1}"
#                             ),
#                         ],
#                         Action(remove_candidates=removed_candidates),
#                     )
#
#     # TODO:
#     # Locked Candidates - untested but should work hopefully
#     # Pointing Tuples - untested and probably needs a little tweaking
#     # Naked Triple
#     # X-Wing
#     # Hidden Triple
#     # Naked Quadruple
#     # Y-Wing
#     # Avoidable Rectangle
#     # XYZ Wing
#     # Hidden Quadruple
#     # Unique Rectangle
#     # Hidden Rectangle
#     # Pointing Rectangle
#     # Swordfish
#     # Jellyfish
#     # Skyscraper
#     # 2-String Kite
#     # Empty Rectangle
#     # Color Chain
#     # Finned X-Wing
#     # Finned Swordfish
#     # Finned Jellyfish
#
#     def hint(self) -> Generator[Technique]:
#         """
#         Search for techniques in approximate order of difficulty
#         Yields:
#             Technique
#         """
#         types = [
#             self._naked_singles,
#             self._hidden_singles,
#             self._naked_pairs,
#             # self._hidden_pairs,
#             # self._locked_candidates,
#             # self._pointing_tuples,
#             self._skyscraper,
#         ]
#         # Maybe doing this async in some way could help. But because if only returns the easiest technique it might not be the easiest to do.
#         # Could potentially start looking for all types at the same time and await them in order of easiest to hardest and return first non-null.
#         # As long as I keep writing the techniques efficiently, using numpy as much as possible it shouldn't really matter if it is async or not but maybe it would with some of the more advanced techniques, like if I do 3d medusa chain analysis.
#         for technique in types:
#             yield from technique()
#
#     def apply_action(self, action: Action) -> None:
#         """
#         Modify cells and candidates based on a Technique's Action
#         Args:
#             action: the Action to apply
#         """
#         if (x := action.get_cells()) is not None:
#             self.add_cells(x)
#
#         if (x := action.get_candidates()) is not None:
#             self.remove_candidates(x)
#
#
# if __name__ == "__main__":
#     board = sudoku.Board(
#         ".18....7..7...19...6.85.12.6..7..3..7..51..8.8.4..97.5.47.98.5...26.5.3...6...24."
#         # "................................................................................1"
#         # "..............................................................................321"
#     )
#
#     board.auto_normal()
#
#     human: HumanSolver = HumanSolver(board)
#
#     for technique in human._hidden_singles():
#         print("found")
#
#     # TODO: tests needed for all techniques. This is probably a higher priority than adding more techniques. Testing properly is tricky because there may be several valid ways to apply the technique and which one gets used really doesn't matter.
#     # techniques are now yielded so tests should check all of them. Although there could maybe be some issues like if a hidden single was hidden single for box and column would that be 1 or 2 techniques.
#
#     # TODO: check Action()'s thoroughly for all techniques.
