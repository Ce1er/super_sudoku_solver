# import line_profiler
from __future__ import annotations
from typing import Literal, Optional, SupportsInt, TypeVar

import numpy as np
import numpy.typing as npt

from abc import ABC
from functools import reduce

import super_sudoku_solver.np_candidates as npc


# TODO: fix types. Mostly which specific np int type? Also consider non-numpy types being passed in such as int to MessageNum
class MessagePart(ABC):
    """
    Base class for parts of message used by Technique
    This class should not be used directly
    """

    _text: str
    _highlight: Optional[int]

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, new: str) -> None:
        if not isinstance(new, str):
            raise TypeError("Message text cannot be set to non-str type")
        self._text = new

    @property
    def highlight(self) -> Optional[int]:
        return self._highlight

    @highlight.setter
    def highlight(self, new: Optional[SupportsInt]) -> None:
        if new is None or isinstance(new, int):
            self._highlight = new
        else:
            try:
                self._highlight = int(new)
            except ValueError:
                raise TypeError("Message highlight could not be interpreted as int")


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


# class MessageCoord(MessagePart):
#     """
#     For a single coordinate
#     """
#
#     def __init__(
#         self, coord: npt.NDArray[np.signedinteger], highlight: Optional[int] = None
#     ) -> None:
#         """
#         Args:
#             coord: 0-based coordinate. size 2 and can be any ndim as long as it can be reshaped to (2,).
#             highlight: highlight group
#         """
#         self._coord = coord
#         coord = np.copy(coord)
#         self.highlight = highlight
#         coord.reshape(2)
#         coord += 1
#         self.text = "Cell ({}, {})".format(*coord)
#
#     @property
#     def coord(self):
#         return self._coord


class MessageCoords(MessagePart):
    """
    For cell coordinates
    """

    def __init__(
        self, coords: npt.NDArray[np.signedinteger], highlight: Optional[int] = None
    ) -> None:
        """
        Args:
            coords: 0 based coordinates. shape (..., 2). Num preceeding 2 can be anything. Anything preceeding that has to be 1.
            highlight: highlight group

        """
        coords = npc.normalise_coords(coords)
        self._coords = coords
        coords = np.copy(coords)
        coords += 1
        self.highlight = highlight
        if len(coords) > 1:
            tmp = "Cells"
            for coord in coords:
                tmp += " ({}, {})".format(*coord)
            self.text = tmp
        else:
            self.text = "Cell ({}, {})".format(*coords[0])

    @property
    def coords(self):
        return self._coords



class MessageNums(MessagePart):
    """
    For several numbers
    """

    def __init__(
        self,
        nums: np.ndarray[tuple[int, Literal[1]], np.dtype[np.integer]] | SupportsInt,
        highlight: Optional[int] = None,
    ) -> None:
        """
        Args:
            nums: numpy array of nums or a single number
            highlight: highlight group
        """
        if not isinstance(nums, np.ndarray):
            nums = np.array([int(nums)])

        self.highlight = highlight

        if nums.size == 1:
            self.text = "number " + str(nums.reshape(1)[0] + 1)
        else:
            tmp = "numbers"
            for num in nums:
                tmp += " " + str(num.reshape(1)[0] + 1)
            self.text = tmp


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
        self._add_cells = add_cells
        self._remove_candidates = remove_candidates

    @property
    def cells(self):
        return self._add_cells

    @property
    def candidates(self):
        return self._remove_candidates

    def __eq__(self, other):
        return (
            other
            and self._add_cells == other.add_cells
            and self._remove_candidates == other.remove_candidates
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        cells = (
            self._add_cells if self._add_cells is None else self._add_cells.tobytes()
        )
        candidates = (
            self._remove_candidates
            if self._remove_candidates is None
            else self._remove_candidates.tobytes()
        )

        return hash((cells, candidates))


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
        self._technique: str = technique
        self._message = message
        self._raw_message: str = reduce(
            lambda prev, next: prev + next._text, message, ""
        )
        self._action: Action = action

    @property
    def action(self) -> Action:
        return self._action

    @property
    def message(self) -> str:
        return self._raw_message

    @property
    def message_parts(self) -> list[T]:
        return self._message

    @property
    def technique(self) -> str:
        return self._technique
