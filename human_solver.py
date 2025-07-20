import numpy as np
import numpy.typing as npt


class Human_Solver:
    def __init__(self, candidates: npt.NDArray) -> None:
        self.candidates = candidates  # 9x9x9

    def _adjacent(
        self, target: npt.NDArray, row=True, column=True, box=True, cage=False
    ):
        """
        Args:
            target: 1x3 array (x, y, number)
            row: whether to scan row or not
            column: whether to scan column or not
            box: whether to scan box or not
            cage: whether to scan cage or not
        Yields:
            {
                "coords": numpy array [x,y],
                "from": where from e.g. "box", "column", "row", "cage",
            }
        """
        # Cage not scanned by default as most techniques don't rely on it
        if row:
            ...  # Yield matches

    def _singles(self): ...
