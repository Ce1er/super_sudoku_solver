# import line_profiler
import copy
import pytest
from sudoku import Board
from human_solver import Human_Solver


@pytest.fixture
def board():
    return Human_Solver(
        Board(
            "1.5..2.84..63.12.7.2..5.....9..1....8.2.3674.3.7.2..9.47...8..1..16..4.926914.37."
        )
    )


# @line_profiler.profile
def apply_all_techniques(board: Human_Solver, max_depth=5, depth=0, seen=None):
    if depth > max_depth:
        return
    board.auto_normal()
    if seen is None:
        seen = set()
    key = board.get_candidates().flatten().tolist()
    i = 0
    for index, value in enumerate(key):
        i |= int(value) << index

    if i in seen:
        return board
    seen.add(i)

    for technique in board.hint():
        # print(technique.message)
        new = copy.deepcopy(board)
        new.apply_action(technique.get_action())
        new.auto_normal()
        if not new.is_valid():
            print(new.cells)
            raise AssertionError(
                f"Technique {technique.get_technique()} produced invalid board."
            )

        if (
            board.get_candidates().tobytes() == new.get_candidates().tobytes()
            and board.cells.tobytes() == new.cells.tobytes()
        ):
            raise AssertionError(
                f"Technique {technique.get_technique()} did not change any candidates"
            )

        apply_all_techniques(new, max_depth, depth+1, seen)


def test_human_techniques(board):
    apply_all_techniques(board)


if __name__ == "__main__":
    apply_all_techniques(
        Human_Solver(
            Board(
                "1.5..2.84..63.12.7.2..5.....9..1....8.2.3674.3.7.2..9.47...8..1..16..4.926914.37."
            )
        )
    )

# TODO: some sort of check which makes sure all varients of each technique are used. e.g. if a technique could be based on row, col or box make sure all 3 are used.
