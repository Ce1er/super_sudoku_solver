import numpy as np

from typing import Literal

type Adjacency = Literal["row", "column", "box"]

# Common array types with shape and dtype.

# Values: [row, column]
type Coord = np.ndarray[tuple[Literal[2]], np.dtype[np.int8]]

type Coords = np.ndarray[tuple[int, Literal[2]], np.dtype[np.int8]]

# Values: [row, column, value]
type Cell = np.ndarray[tuple[Literal[3]], np.dtype[np.int8]]

# Indexes: [row, column]
type Cells = np.ndarray[tuple[Literal[9], Literal[9]], np.dtype[np.int8]]
type CellCandidates = np.ndarray[tuple[Literal[9]], np.dtype[np.bool]]

# Indexes: [value, row, column]
type Candidates = np.ndarray[
    tuple[Literal[9], Literal[9], Literal[9]], np.dtype[np.bool]
]
