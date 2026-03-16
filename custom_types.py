import numpy as np
from typing import Literal

Adjacency = Literal["row", "column", "box"]

# Common array types with shape and dtype.

# Values: [row, column]
Coord = np.ndarray[tuple[Literal[2]], np.dtype[np.int8]]

# Values: [row, column, value]
Cell = np.ndarray[tuple[Literal[3]], np.dtype[np.int8]]

# Indexes: [row, column]
Cells = np.ndarray[tuple[Literal[9], Literal[9]], np.dtype[np.int8]]
CellCandidates = np.ndarray[tuple[Literal[9]], np.dtype[np.bool]]

# Indexes: [value, row, column]
Candidates = np.ndarray[tuple[Literal[9], Literal[9], Literal[9]], np.dtype[np.bool]]
