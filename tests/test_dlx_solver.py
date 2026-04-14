import pytest
from super_sudoku_solver.sudoku import Board, InvalidBoard
from super_sudoku_solver.save_manager import Puzzle
import super_sudoku_solver.dlx_solver as dlx_solver
from uuid import uuid7

@pytest.fixture
def node():
    return dlx_solver.Node()


@pytest.fixture
def header_node():
    return dlx_solver.HeaderNode(0)


@pytest.mark.parametrize("node", ["node", "header_node"], indirect=True)
def test_node(node):
    assert node.right is node.left is node.up is node.down is node


@pytest.fixture()
def matrix_unique_solution():
    return dlx_solver.Matrix(
        [1, 2, 3, 4, 5, 6, 7],
        [[1, 4, 7], [1, 4], [4, 5, 7], [3, 5, 6], [2, 3, 6, 7], [2, 7]],
    )


def test_solve_unique_solution(matrix_unique_solution):
    assert list(matrix_unique_solution.generate_solutions()) == [
        [[1, 4], [5, 6, 3], [2, 7]]
    ]


@pytest.fixture
def board():
    puzzle = Puzzle(
        str(uuid7()),
        ".83..241.2.4..5....1..74.283..49.15...7.1...69..753.8.84....6..5...4..31136.2.5..",
        "easy",
    )
    return Board(puzzle)


@pytest.fixture
def invalid_puzzle():
    puzzle = Puzzle(
        str(uuid7()),
        "183..241.2.4..5....1..74.283..49.15...7.1...69..753.8.84....6..5...4..31136.2.5..",
        "medium",
    )
    return puzzle


@pytest.fixture
def multiple_solutions_puzzle():
    puzzle = Puzzle(
        str(uuid7()),
        ".83...4..2.4..5....1..74..83.....15...7.1...69..753.8.84....6..5...4..31136.2.5..",
        "hard",
    )
    return puzzle


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


def test_no_solutions_board(invalid_puzzle):
    with pytest.raises(InvalidBoard):
        Board(invalid_puzzle)

def test_multiple_solutions_board(multiple_solutions_puzzle):
    with pytest.raises(InvalidBoard):
        Board(multiple_solutions_puzzle)
