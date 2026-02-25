import numpy as np
from typing import Literal

Adjacency = Literal["row", "column", "box"]
Coord = np.ndarray[tuple[Literal[2]], np.dtype[np.int8]]
Cells = np.ndarray[tuple[Literal[9], Literal[9]], np.dtype[np.int8]]
CellCandidates = np.ndarray[tuple[Literal[9]], np.dtype[np.bool]]
Candidates = np.ndarray[tuple[Literal[9], Literal[9], Literal[9]], np.dtype[np.bool]]
