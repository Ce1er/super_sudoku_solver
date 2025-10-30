import numpy as np
from numpy._typing import NDArray
import numpy.typing as npt


def adjacent_row(coords: npt.NDArray[np.int8]) -> npt.NDArray[np.bool]:
    """
    Args:
        coords: [[row, column], [row, column]...] (0-based indexing). Column is required but will not change return value so can be set arbitrarily.
    Returns:
        9x9 Boolean array where True represents cells in rows from coords given
    """
    if coords.ndim == 1:
        coords = coords.reshape((1, 2))
    elif coords.ndim > 2:
        coords = coords.reshape((coords.shape[-2], 2))
    elif coords.ndim == 2:
        pass
    else:
        raise ValueError(f"coords have invalid dimension {coords.ndim}")

    assert coords.ndim == 2, "np_candidates.adjacent_row failed to interpret coords"

    board = np.full((9, 9), False, dtype=bool)
    rows = coords[:, 0]
    board[rows, :] = True
    return board


def adjacent_column(coords: npt.NDArray[np.int8]) -> npt.NDArray[np.bool]:
    """
    Args:
        coords: [[row, column], [row, column]...] (0-based indexing). Row is required but will not change return value so can be set arbitrarily.
    Returns:
        9x9 Boolean array where True represents cells in columns from coords given
    """
    if coords.ndim == 1:
        coords = coords.reshape((1, 2))
    elif coords.ndim > 2:
        coords = coords.reshape((coords.shape[-2], 2))
    elif coords.ndim == 2:
        pass
    else:
        raise ValueError(f"coords have invalid dimension {coords.ndim}")

    assert coords.ndim == 2, "np_candidates.adjacent_column failed to interpret coords"
    board = np.full((9, 9), False, dtype=bool)
    columns = coords[:, 1]
    board[:, columns] = True
    return board


def adjacent_box(coords: npt.NDArray[np.int8]) -> npt.NDArray[np.bool]:
    """
    Args:
        coords: [[row, column], [row, column]...] (0-based indexing).
    Returns:
        9x9 Boolean array where True represents cells in boxes from coords given
    """
    if coords.ndim == 1:
        coords = coords.reshape((1, 2))
    elif coords.ndim > 2:
        coords = coords.reshape((coords.shape[-2], 2))
    elif coords.ndim == 2:
        pass
    else:
        raise ValueError(f"coords have invalid dimension {coords.ndim}")

    assert coords.ndim == 2, "np_candidates.adjacent_box failed to interpret coords"
    board = np.full((9, 9), False, dtype=bool)
    for coord in coords:
        board[
            3 * (coord[0] // 3) : 3 * (coord[0] // 3) + 3,
            3 * (coord[1] // 3) : 3 * (coord[1] // 3) + 3,
        ] = True
    return board


def adjacent(coords: npt.NDArray[np.int8]) -> npt.NDArray[np.bool]:
    """
    Args:
        coords: [[row, column], [row, column]...] (0-based indexing).
    Returns:
        9x9 Boolean array where True represents cells in boxes from coords given
    """
    if coords.ndim == 1:
        coords = coords.reshape((1, 2))
    elif coords.ndim > 2:
        coords = coords.reshape((coords.shape[-2], 2))
    elif coords.ndim == 2:
        pass
    else:
        raise ValueError(f"coords have invalid dimension {coords.ndim}")

    assert coords.ndim == 2, "np_candidates.adjacent failed to interpret coords"
    return adjacent_row(coords) | adjacent_column(coords) | adjacent_box(coords)
