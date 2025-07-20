import pytest
import dlx_solver
import sudoku


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


# TODO:
# * Multiple solution tests
# * Test Matrix() methods seperately
# * Test datatypes


@pytest.fixture
def board():
    return sudoku.Board(
        "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4.."
    )
