import numpy as np
import numpy.typing as npt

from functools import wraps
import itertools
from itertools import combinations
import abc
from typing import Literal, SupportsInt, Self, Callable, assert_never
from collections.abc import Generator

from super_sudoku_solver.custom_types import (
    Adjacency,
    Coord,
    Cells,
    CellCandidates,
    Candidates,
)
import super_sudoku_solver.np_candidates as npc
from super_sudoku_solver.human_solver import (
    MessagePart,
    Technique,
    Action,
    MessageCoords,
    MessageNums,
    MessageText,
)


class _TechniqueInstance(abc.ABC):
    """
    Base class for all human technique instances to hold information
    about how the technique can be used on board.
    """

    NAME: str

    @property
    def name(self) -> str:
        return self.NAME

    @abc.abstractmethod
    def _generate_action(self) -> Action: ...

    @abc.abstractmethod
    def _generate_message(self) -> list[MessagePart]: ...

    @property
    def technique(self) -> Technique:
        return Technique(self.NAME, self._generate_message(), self._generate_action())


class _TechniqueFinder(abc.ABC):
    """
    Base class for all human technique finders to find technique instances
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

        # Subclasses of this find techniques, they don't apply them
        # So these shouldn't change
        self._candidates.flags.writeable = False
        self._clues.flags.writeable = False
        self._guesses.flags.writeable = False
        self._cells.flags.writeable = False

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

    def _non_null_actions(
        func: Callable[[Self], Generator[Technique]],
    ) -> Callable[[Self], Generator[Technique]]:  # type: ignore[misc]
        """
        Decorator to filter Techniques to only include ones where the action has an effect on candidates and/or cells.
        Slightly simplifies technique detection as those functions are not responsible for checking if it has an effect or not.
        Yields:
            Techniques it is given that have an effect on the board
        """

        # @wraps preserves dunder attributes of decorated functions
        # without it those attributes would refer to wrapper() instead
        @wraps(func)
        def wrapper(self: Self) -> Generator[Technique]:
            for technique in func(self):
                if not self._action_is_null(technique.action):
                    yield technique

        return wrapper

    def _non_duplicate_actions(
        func: Callable[[Self], Generator[Technique]],
    ) -> Callable[[Self], Generator[Technique]]:  # type: ignore[misc]
        """
        Decorator to filter out duplicate techniques.
        Duplicates are techniques of the same type with an identical action.
        Their message does not have to be identical.
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
        """
        Args:
            coord: coordinate of naked single
            num: value that should be at coordinate
        """
        self._coord = coord
        self._num = num

    def _generate_action(self):
        new_cells = np.full((9, 9), -1, dtype=np.int8)
        new_cells[*self._coord] = self._num
        return Action(new_cells)

    def _generate_message(self):
        return [
            MessageCoords(self._coord, highlight=1),
            MessageText("is"),
            MessageNums(self._num),
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
        # TODO: attrs should probably be public from _TechniqueFinder as properties maybe

        # Naked singles have exactly one candidate in a cell
        naked_singles: Cells = (
            np.add.reduce(self._candidates, axis=0, dtype=np.int8) == 1
        )
        for coord in npc.argwhere(naked_singles):
            row, column = coord
            num = npc.argwhere(self._candidates[:, row, column]).flatten()[0]

            yield _NakedSinglesInstance(coord, num)


class _HiddenSinglesInstance(_TechniqueInstance):
    NAME = "Hidden Singles"

    def __init__(self, coord: Cell, adjacency: Adjacency):
        """
        Args:
            coord: coordinate of hidden single and its value
            adjacency: the adjacency in which it is a single
        """
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

        return [
            MessageCoords(self._coord[1:], highlight=1),
            MessageText("is"),
            MessageNums(self._coord[0]),
            MessageText("because there are no others cells that can be"),
            MessageNums(self._coord[0]),
            MessageText(f"in the {self._adjacency}."),
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
            npc.adjacent_row: "row",
            npc.adjacent_column: "column",
            npc.adjacent_box: "box",
        }  # TODO: make this a class constant, and probably worth switching keys and values
        for coord in npc.argwhere(self._candidates):
            num, row, column = coord
            for func, adjacency in types.items():
                adjacent = func(coord[1:3]) & self._candidates[num]
                candidates_at_cell: CellCandidates = self._candidates[:, row, column]

                # Check it is single and not naked
                if not (
                    np.count_nonzero(adjacent) == 1
                    and len(npc.argwhere(candidates_at_cell)) != 1
                ):
                    continue

                yield _HiddenSinglesInstance(coord, adjacency)


class _NakedPairsInstance(_TechniqueInstance):
    NAME = "Naked Pairs"

    def _get_remove_from(self):
        """
        Returns:
            adjacency(s) candidates should be removed from
        """
        remove_from = []
        for adjacency, func in self._types.items():
            if func(self._cell1[0:2])[*self._cell2]:
                remove_from.append(adjacency)
        return remove_from

    def __init__(self, pair, nums, cell1, cell2, types, candidates):
        self._pair = pair
        self._nums = nums
        self._cell1 = cell1
        self._cell2 = cell2
        self._types = types
        self._candidates = candidates
        self._remove_from = self._get_remove_from()

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
            MessageText("are"),
            MessageNums(npc.argwhere(self._nums)),
            MessageText("so any cells adjacent to both"),
            MessageCoords(np.array([*self._pair]), highlight=1),
            MessageText("can have"),
            MessageNums(npc.argwhere(self._nums)),
            MessageText("removed as candidates."),
        ]

    def _generate_action(self):
        remove_adjacencies = self._remove_from
        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
        for adjacency in remove_adjacencies:
            removed_candidates[self._nums] |= self._types[adjacency](self._cell1[0:2])

        removed_candidates &= self._candidates

        removed_candidates[:, self._cell1[0], self._cell1[1]] = False
        removed_candidates[:, self._cell2[0], self._cell2[1]] = False

        return Action(remove_candidates=removed_candidates)


class NakedPairs(_TechniqueFinder):
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
            "row": npc.adjacent_row,
            "column": npc.adjacent_column,
            "box": npc.adjacent_box,
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
            if not npc.adjacent(cell1[0:2])[*cell2]:
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
    NAME = "Hidden Pairs"

    def __init__(self, cells, num_pair, adjacent_by):
        self._cells = cells
        self._num_pair = num_pair
        self._adjacent_by = adjacent_by

    def _generate_message(self):
        return [
            MessageCoords(self._cells, highlight=1),
            MessageText("are the only cells that can be"),
            MessageNums(self._num_pair),
            MessageText(
                "in their "
                + ", ".join(self._adjacent_by)
                + " so we can remove all other candidates from them."
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
            "row": npc.adjacent_row,
            "column": npc.adjacent_column,
            "box": npc.adjacent_box,
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
            if not npc.adjacent(cell1)[*cell2]:
                continue

            # Pair is hidden so all potential pairs must be checked
            for num_pair in combinations(common_nums, r=2):
                num_pair = np.array([*num_pair])
                adjacent_by = []
                for adjacency, func in types.items():
                    # If cells are adjacent by adjacency append adjacency to adjacent_by
                    if func(cell1)[*cell2]:
                        adjacent_by.append(adjacency)

                temp = adjacent_by.copy()
                # 9x9 array where True means either (or both) nums are there
                other_occurences = np.logical_or.reduce(self._candidates[num_pair])
                for adjacency in adjacent_by:
                    func = types[adjacency]
                    if np.count_nonzero(func(cell1) & other_occurences) != 2:
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
            # If there's more that 1 coord use plural
            (
                MessageText("are the only cells that can be")
                if self._coords.size > 2
                else MessageText("is the only cell that can be")
            ),
            MessageNums(self._num),
            MessageText(
                f"in {'their' if self._coords.size > 2 else 'its'} {self._adjacency} so"
            ),
            MessageNums(self._num),
            MessageText(
                "can be removed as a candidate from the other cells in their house."
            ),
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
        for num in range(9):
            for coords in combinations(
                npc.argwhere(self._candidates[num]), r=self.count
            ):
                coords = np.array([*coords])

                # Check exactly the right number of cells with num are in box
                # And that both coords are in the same box
                if (
                    np.count_nonzero(
                        self._candidates[num] & npc.adjacent_box(coords, -1)
                    )
                    != self.count
                ):
                    continue

                columns = np.count_nonzero(npc.adjacent_column(coords)) // 9
                rows = np.count_nonzero(npc.adjacent_row(coords)) // 9

                if columns == self.count and rows == 1:
                    direction = "row"
                elif rows == self.count and columns == 1:
                    direction = "column"
                else:
                    continue

                yield {"coords": coords, "num": num, "direction": direction}


class _PointingTuplesInstance(_TechniqueInstance):
    def __init__(self, coords, num, direction) -> None:
        self.coords = coords
        self.num = num
        self.direction = direction

    def _generate_message(self):
        return [
            MessageCoords(self.coords, highlight=1),
            MessageText("are the only cells that can be"),
            MessageNums(self.num),
            MessageText(
                f"in their box and they share a {self.direction} so we can remove other options from their {self.direction}."
            ),
        ]

    def _generate_action(self):
        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)
        func = npc.adjacent_row if self.direction == "row" else npc.adjacent_column

        removed_candidates[self.num, :, :] |= func(self.coords)
        for coord in self.coords:
            removed_candidates[self.num, coord[0], coord[1]] = False

        return Action(remove_candidates=removed_candidates)


class _PointingPairsInstance(_PointingTuplesInstance):
    NAME = "Pointing Pairs"

    def __init__(self, coords, num, direction) -> None:
        super().__init__(coords, num, direction)


class _PointingTriplesInstance(_PointingTuplesInstance):
    NAME = "Pointing Triples"

    def __init__(self, coords, num, direction) -> None:
        super().__init__(coords, num, direction)


class PointingPairs(_PointingTuples, _TechniqueFinder):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray,
        guesses: npt.NDArray[np.int8],
    ):
        _TechniqueFinder.__init__(self, candidates, clues, guesses)
        _PointingTuples.__init__(self, candidates, clues, guesses, 2)

    def _find(self):
        for pair in self.partially_find():
            coords = pair["coords"]
            num = pair["num"]
            direction = pair["direction"]
            yield _PointingPairsInstance(coords, num, direction)


class PointingTriples(_PointingTuples, _TechniqueFinder):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray,
        guesses: npt.NDArray[np.int8],
    ):
        _TechniqueFinder.__init__(self, candidates, clues, guesses)
        _PointingTuples.__init__(self, candidates, clues, guesses, 3)

    def _find(self):
        for pair in self.partially_find():
            coords = pair["coords"]
            num = pair["num"]
            direction = pair["direction"]
            yield _PointingTriplesInstance(coords, num, direction)


class _SkyscraperInstance(_TechniqueInstance):
    NAME = "Skyscrapers"

    def __init__(
        self,
        non_shared_cell1,
        non_shared_cell2,
        shared_cell1,
        shared_cell2,
        num,
        adjacency,
        other_adjacency,
        candidates,
    ):
        """
        Args:
            non_shared_cell{1,2}: the two cells which don't share a row/column
            shared_cell{1,2}: the two cells which share a row/column
            num: the number skyscraper will remove candidates for
            adjacency: the adjacency shared cells don't share
            other_adjacency: the adjacency shared cells do share
            candidates: candidates of board
        """
        self._non_shared_cell1 = non_shared_cell1
        self._non_shared_cell2 = non_shared_cell2
        self._shared_cell1 = shared_cell1
        self._shared_cell2 = shared_cell2
        self._num = num
        self._adjacency = adjacency
        self._other_adjacency = other_adjacency
        self._candidates = candidates

    def _generate_message(self):
        return [
            MessageText("At least one of"),
            MessageCoords(
                np.array([self._non_shared_cell1, self._non_shared_cell2]), highlight=1
            ),
            MessageText("must be"),
            MessageNums(self._num),
            MessageText("because they are the only"),
            MessageNums(self._num),
            MessageText(f"in their {self._adjacency} except these"),
            MessageCoords(
                np.array([self._shared_cell1, self._shared_cell2]), highlight=2
            ),
            MessageText(
                f"which share a {self._other_adjacency}. That means any cells that see both"
            ),
            MessageCoords(
                np.array([self._non_shared_cell1, self._non_shared_cell2]), highlight=1
            ),
            MessageText("can't be"),
            MessageNums(self._num),
            MessageText("."),
        ]

    def _generate_action(self):
        removed_candidates = np.full((9, 9, 9), False, dtype=np.bool)

        current = np.full((9, 9), False, dtype=np.bool)
        current[*self._non_shared_cell1] = True
        current[*self._non_shared_cell2] = True

        # Remove candidates that can see both non-shared cells
        removed_candidates[self._num] = (
            self._candidates[self._num]
            & npc.adjacent(
                np.array([self._non_shared_cell1, self._non_shared_cell2]), -1
            )
            & ~current
        )

        return Action(remove_candidates=removed_candidates)


class Skyscrapers(_TechniqueFinder):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

    def _find(self: Self):
        """
        Search for skyscrapers based on candidates
        Yields:
            Technique
        """
        types = ["column", "row"]

        for adjacency in types:
            for num in range(9):
                # Find rows or columns with 2 occurences of num.
                if adjacency == "column":
                    # List of all columns where each item is the number of occurences of num
                    columns = np.add.reduce(
                        self._candidates[num], axis=0, dtype=np.int8
                    )

                    # Convert to boolean array representing valid columns
                    potential = npc.argwhere(columns == 2)
                elif adjacency == "row":
                    # List all rows where each item is the number of occurences of num
                    rows = np.add.reduce(self._candidates[num], axis=1, dtype=np.int8)

                    # Convert to boolean array representing valid rows
                    potential = npc.argwhere(rows == 2)
                else:
                    assert False, "types has invalid key"

                # There must be at least 2 rows/columns
                if potential.size < 2:
                    continue

                # Try every pairing of row or column
                for pairing in combinations(potential, r=2):
                    totals: np.ndarray[tuple[Literal[1], Literal[9]], np.dtype[np.int8]]
                    if adjacency == "column":
                        columns = self._candidates[num, :, pairing]

                        # The total occurences of num in each row
                        # Only counting occurences in either column in pairing
                        totals = np.add.reduce(columns, axis=0, dtype=np.int8)
                    elif adjacency == "row":
                        rows = self._candidates[num, pairing, :]

                        # The total occurences of num in each column
                        # Only counting occurences in either row in pairing
                        totals = np.add.reduce(rows, axis=0, dtype=np.int8)
                    else:
                        raise AssertionError

                    shared = totals == 2
                    non_shared = totals == 1

                    # Check that one pair of candidates share a row/column
                    # And the other pair doesn't
                    if not (
                        np.count_nonzero(non_shared) == 2
                        and np.count_nonzero(shared) == 1
                    ):
                        continue

                    # Find cells that see both of the cells in the non_shared rows/columns
                    # Any cells that do see both can have num removed as a candidate
                    if adjacency == "column":
                        rows = self._candidates[num, :, pairing] & ~shared
                        row1 = rows[0][0]
                        row2 = rows[1][0]
                        cell1_row = npc.argwhere(row1)[0][0]
                        cell2_row = npc.argwhere(row2)[0][0]

                        non_shared_cell1 = np.array([cell1_row, pairing[0][0]])
                        non_shared_cell2 = np.array([cell2_row, pairing[1][0]])

                        # Will be the same for the other 2 because they have to share a row
                        shared_row = self._candidates[num, :, pairing] & ~non_shared
                        shared_row = npc.argwhere(shared_row[0][0])[0][0]

                        shared_cell1 = np.array([shared_row, pairing[0][0]])
                        shared_cell2 = np.array([shared_row, pairing[1][0]])

                    elif adjacency == "row":
                        non_shared_columns = self._candidates[num, pairing, :] & ~shared
                        col1 = non_shared_columns[0][0]
                        col2 = non_shared_columns[1][0]

                        non_shared_cell1_col = npc.argwhere(col1)[0][0]
                        non_shared_cell2_col = npc.argwhere(col2)[0][0]

                        # Cells which must be a certain number
                        non_shared_cell1 = np.array(
                            [pairing[0][0], non_shared_cell1_col]
                        )
                        non_shared_cell2 = np.array(
                            [pairing[1][0], non_shared_cell2_col]
                        )

                        # Will be the same for the other 2 because they have to share a column
                        shared_column = self._candidates[num, pairing, :] & ~(
                            non_shared
                        )
                        shared_column = npc.argwhere((shared_column)[0][0])[0][0]

                        # Cells which share a column
                        shared_cell1 = np.array([pairing[0][0], shared_column])
                        shared_cell2 = np.array([pairing[1][0], shared_column])
                    else:
                        assert False, "types has invalid key"

                    other_adjacency = "row" if adjacency == "column" else "column"

                    yield _SkyscraperInstance(
                        non_shared_cell1,
                        non_shared_cell2,
                        shared_cell1,
                        shared_cell2,
                        num,
                        adjacency,
                        other_adjacency,
                        self._candidates,
                    )


class _XWingInstance(_TechniqueInstance):
    NAME = "X-Wings"

    def __init__(self, adjacency, pairing, num, arr) -> None:
        self.adjacency = adjacency
        self.pairing = np.array(pairing).flatten()
        self.num = num
        self.arr = arr
        self.indices = np.array(npc.argwhere(self.arr).flatten(), dtype=np.int8)

    def _generate_action(self):

        remove_candidates = np.full((9, 9, 9), False, dtype=np.bool)

        # Candidates will be removed in opposite direction to adjacency
        if self.adjacency == "column":
            remove_candidates[self.num, self.indices, :] = True

            coords = itertools.product(self.indices, self.pairing)
            for coord in coords:
                # Don't remove candidates for the cells that are part of the X-Wing
                remove_candidates[self.num, coord[0], coord[1]] = False

        elif self.adjacency == "row":
            remove_candidates[self.num, :, self.indices] = True

            coords = itertools.product(self.pairing, self.indices)
            for coord in coords:
                # Don't remove candidates for the cells that are part of the X-Wing
                remove_candidates[self.num, coord[0], coord[1]] = False

        return Action(remove_candidates=remove_candidates)

    def _generate_message(self):
        # Coordinates of all 4 cells

        if self.adjacency == "row":
            coords = np.array(
                list(
                    map(
                        lambda x: np.array(list(map(np.int8, x))),
                        itertools.product(self.pairing, self.indices),
                    )
                )
            )
            rows = list(set(coords[:, 0]))
            group_1 = coords[coords[:, 0] == rows[0]]
            group_2 = coords[coords[:, 0] == rows[1]]
            other_adjacency = "column"

        elif self.adjacency == "column":
            coords = np.array(
                list(
                    map(
                        lambda x: np.array(list(map(np.int8, x))),
                        itertools.product(self.indices, self.pairing),
                    )
                )
            )
            columns = list(set(coords[:, 1]))
            group_1 = coords[coords[:, 1] == columns[0]]
            group_2 = coords[coords[:, 1] == columns[1]]
            other_adjacency = "row"
        else:
            assert_never(self.adjacency)

        return [
            MessageCoords(group_1, highlight=1),
            MessageText("and"),
            MessageCoords(group_2, highlight=2),
            MessageText("are the only"),
            MessageNums(self.num),
            MessageText(f"s in their {self.adjacency}s so"),
            MessageNums(self.num),
            MessageText(
                f"can be removed as a candidate from all other cells in their {other_adjacency}s."
            ),
        ]


class XWing(_TechniqueFinder):
    def __init__(
        self,
        candidates: npt.NDArray[np.bool],
        clues: npt.NDArray[np.int8],
        guesses: npt.NDArray[np.int8],
    ):
        super().__init__(candidates, clues, guesses)

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
            "column": npc.adjacent_column,
            "row": npc.adjacent_row,
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
                    if adjacency == "column":
                        arr = self._candidates[num, :, pairing]
                    if adjacency == "row":
                        arr = self._candidates[num, pairing, :]

                    if not np.array_equal(arr[0], arr[1]):
                        continue

                    yield _XWingInstance(adjacency, pairing, num, arr[0].flatten())


TECHNIQUES = [
    NakedSingles, 
    HiddenSingles, 
    NakedPairs, 
    HiddenPairs, 
    LockedCandidates, 
    Skyscrapers,
    PointingPairs,
    PointingTriples,
    XWing,
]
