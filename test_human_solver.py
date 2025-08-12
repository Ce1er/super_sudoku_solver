import pytest
from human_solver import Human_Solver, Technique
from sudoku import Board
import numpy as np


@pytest.fixture
def board():
    return Human_Solver(
        Board(
            ".18....7..7...19...6.85.12.6..7..3..7..51..8.8.4..97.5.47.98.5...26.5.3...6...24."
        )
    )


def test_naked_single(board):
    assert (
        board._naked_singles() == ...
    )  # Something to check (2,8) is 6, message may be changed so relying on that isn't great
    # Eventually the human solver will be able to fully solve puzzles and then that could make a good test case, wouldn't be great for seeing what caused the problem but at least it would mostly confirm if it works
