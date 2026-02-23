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

    _text: str
    _highlight: Optional[int]

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, new: str) -> None:
        self._text = new

    @property
    def highlight(self) -> Optional[int]:
        return self._highlight

    @highlight.setter
    def highlight(self, new: Optional[int]) -> None:
        self._highlight = new


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
        self._text = text
        self._highlight = highlight


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
        self._highlight = highlight
        coord.reshape(2)
        coord += 1
        self._text = "Cell ({}, {})".format(*coord)


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
        self._highlight = highlight
        tmp = "Cells"
        coords += 1
        for coord in coords:
            tmp += " ({}, {})".format(*coord.reshape(2))
        self._text = tmp


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
        self._highlight = highlight

        if isinstance(num, np.ndarray):
            self._text = "number " + str(num.reshape(1)[0] + 1)
        else:
            self._text = "number " + str(num + 1)


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
        self._highlight = highlight
        tmp = "numbers"
        for num in nums:
            tmp += " " + str(num.reshape(1)[0] + 1)
        self._text = tmp


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
        self._highlight = highlight
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

    def __eq__(self, other):
        return (
            other
            and self.add_cells == other.add_cells
            and self.remove_candidates == other.remove_candidates
        )

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        cells = self.add_cells if self.add_cells is None else self.add_cells.tobytes()
        candidates = (
            self.remove_candidates
            if self.remove_candidates is None
            else self.remove_candidates.tobytes()
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

        # TODO: highlights are ignored rewrite in a way that actually uses them.
        self._message: str = reduce(lambda prev, next: prev + next._text, message, "")
        self._action: Action = action

    @property
    def action(self) -> Action:
        return self._action

    @property
    def message(self) -> str:
        return self._message

    @property
    def technique(self) -> str:
        return self._technique
