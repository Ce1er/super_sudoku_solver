import pytest
from test_utils import valid_sudoku
from sudoku import Board

@pytest.fixture
def board():
    return Board(
        "................................................................................."
    )

def test_valid_solutions(board):
    n = 0
    for solution in board.solve():
        n += 1
        assert valid_sudoku(solution) 
        print(n)
        if n > 1000:
            break

