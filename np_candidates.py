from collections.abc import Callable
import numpy as np
from numpy._typing import NDArray
import numpy.typing as npt


def adjacent_row(
    coords: npt.NDArray[np.int8], to_n: int = 1, strict: bool = False
) -> npt.NDArray[np.bool]:
    """
    Args:
        coords: [[row, column], [row, column]...] (0-based indexing). Column is required but will not change return value so can be set arbitrarily.
        to_n: how many of the coords given need to be adjacent to. (-1 for adjacent to all)
        strict: True means most be adjacent to exactly {to_n} coords. False means {to_n} or more.
    Returns:
        9x9 Boolean array where True represents cells in rows from coords given
    """
    if coords.shape[0] > 256:
        raise ValueError("Too many coords given")

    if coords.ndim == 1:
        coords = coords.reshape((1, 2))
    elif coords.ndim > 2:
        coords = coords.reshape((coords.shape[-2], 2))
    elif coords.ndim == 2:
        pass

    if coords.ndim != 2:
        raise ValueError("Invalid coords")

    board = np.full((coords.shape[0], 9, 9), False, dtype=np.bool)
    for x in range(coords.shape[0]):
        board[x, coords[x, 0]] = True

    counts = np.add.reduce(board, axis=0, dtype=np.uint8)
    if strict:
        mask = counts == to_n
    else:
        mask = counts >= to_n

    return mask


def adjacent_column(
    coords: npt.NDArray[np.int8], to_n: int = 1, strict: bool = False
) -> npt.NDArray[np.bool]:
    """
    Args:
        coords: [[row, column], [row, column]...] (0-based indexing). Row is required but will not change return value so can be set arbitrarily.
        to_n: how many of the coords given need to be adjacent to. (-1 for adjacent to all)
        strict: True means most be adjacent to exactly {to_n} coords. False means {to_n} or more.
    Returns:
        9x9 Boolean array where True represents cells in columns from coords given
    """
    if coords.shape[0] > 256:
        raise ValueError("Too many coords given")
    if coords.ndim == 1:
        coords = coords.reshape((1, 2))
    elif coords.ndim > 2:
        coords = coords.reshape((coords.shape[-2], 2))
    elif coords.ndim == 2:
        pass

    if coords.ndim != 2:
        raise ValueError("Invalid coords")

    board = np.full((coords.shape[0], 9, 9), False, dtype=np.bool)
    for x in range(coords.shape[0]):
        board[x, :, coords[x, 1]] = True

    counts = np.add.reduce(board, axis=0, dtype=np.uint8)
    if strict:
        mask = counts == to_n
    else:
        mask = counts >= to_n

    return mask


def adjacent_box(
    coords: npt.NDArray[np.int8], to_n: int = 1, strict: bool = False
) -> npt.NDArray[np.bool]:
    """
    Args:
        coords: [[row, column], [row, column]...] (0-based indexing).
        to_n: how many of the coords given need to be adjacent to. (-1 for adjacent to all)
        strict: True means most be adjacent to exactly {to_n} coords. False means {to_n} or more.
    Returns:
        9x9 Boolean array where True represents cells in boxes from coords given
    """
    if coords.shape[0] > 256:
        raise ValueError("Too many coords given")

    if coords.ndim == 1:
        coords = coords.reshape((1, 2))
    elif coords.ndim > 2:
        coords = coords.reshape((coords.shape[-2], 2))
    elif coords.ndim == 2:
        pass

    if coords.ndim != 2:
        raise ValueError("Invalid coords")

    board = np.full((coords.shape[0], 9, 9), False, dtype=np.bool)
    for x in range(coords.shape[0]):
        board[
            x,
            3 * (coords[x, 0] // 3) : 3 * (coords[x, 0] // 3) + 3,
            3 * (coords[x, 1] // 3) : 3 * (coords[x, 1] // 3) + 3,
        ] = True

    counts = np.add.reduce(board, axis=0, dtype=np.uint8)
    if strict:
        mask = counts == to_n
    else:
        mask = counts >= to_n

    return mask


def adjacent(
    coords: npt.NDArray[np.int8],
    to_n: int = 1,
    strict: bool = False,
    any_adjacency: bool = True,
) -> npt.NDArray[np.bool]:
    """
    Args:
        coords: [[row, column], [row, column]...] (0-based indexing).
        to_n: how many of the coords given need to be adjacent to. (-1 for adjacent to all)
        strict: True means most be adjacent to exactly {to_n} coords. False means {to_n} or more.
        any_adjacency: True is logical or of all adjacency types, False is logical and.
    Returns:
        9x9 Boolean array where True represents cells in boxes from coords given
    """
    if coords.shape[0] > 256:
        raise ValueError("Too many coords given")
    if coords.ndim == 1:
        coords = coords.reshape((1, 2))
    elif coords.ndim > 2:
        coords = coords.reshape((coords.shape[-2], 2))
    elif coords.ndim == 2:
        pass

    if coords.ndim != 2:
        raise ValueError("Invalid coords")

    funcs: list[Callable[[npt.NDArray[np.int8], int, bool], npt.NDArray[np.bool]]] = [
        adjacent_row,
        adjacent_box,
        adjacent_column,
    ]
    mask = np.full((9, 9), not any_adjacency, dtype=np.bool)
    for func in funcs:
        if any_adjacency:
            mask |= func(coords, to_n, strict)
        else:
            mask &= func(coords, to_n, strict)

    return mask
