import numpy as np
import pytest
from sudoku import Board


@pytest.fixture
def board():
    return Board(
        ".83..241.2.4..5....1..74.283..49.15...7.1...69..753.8.84....6..5...4..31136.2.5.."
    )


def test_dlx_board_solve(board):
    n = 0
    for solution in board.solve():
        # fmt: off
        assert solution.tolist() == [
            [ 6, 7, 2, 8, 5, 1, 3, 0, 4 ],
            [ 1, 8, 3, 0, 7, 4, 6, 5, 2 ],
            [ 5, 0, 4, 2, 6, 3, 8, 1, 7 ],
            [ 2, 1, 7, 3, 8, 5, 0, 4, 6 ],
            [ 3, 4, 6, 1, 0, 7, 2, 8, 5 ],
            [ 8, 5, 0, 6, 4, 2, 1, 7, 3 ],
            [ 7, 3, 8, 4, 2, 0, 5, 6, 1 ],
            [ 4, 6, 1, 5, 3, 8, 7, 2, 0 ],
            [ 0, 2, 5, 7, 1, 6, 4, 3, 8 ],
        ]
        # fmt: on
        n += 1

    assert n == 1
