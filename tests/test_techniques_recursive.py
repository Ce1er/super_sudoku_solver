import pytest
from uuid import uuid7
import copy
from collections import defaultdict
import sys

from super_sudoku_solver.save_manager import Puzzle
from super_sudoku_solver.sudoku import Board
from super_sudoku_solver.paths import RUNTIME_DIR


# Fixture represents all of these boards
@pytest.fixture(
    params=[
        ".83..241.2.4..5....1..74.283..49.15...7.1...69..753.8.84....6..5...4..31136.2.5..",
        "..9.7.....8.4.......3....281.....67..2..13.4..4...78..6...3.....1.............284",
        "8..........36......7..9.2...5...7.......457.....1...3...1....68..85...1..9....4..",
    ]
)
def board(request):
    return Board(
        Puzzle(
            str(uuid7()),
            request.param,
            "easy",
            RUNTIME_DIR,
        )
    )


def test_apply_all_techniques(board):
    """
    Apply all available techniques then apply all available techniques on each new board recursively.
    If any technique applied creates an invalid board this will fail.
    """
    technique_applications = defaultdict(int)

    def helper(
        board,
        max_depth=sys.getrecursionlimit(),
        depth=0,
        seen=None,
        max_technique_applications=100,
    ):
        """
        Args:
            max_technique_applications: maximum number of times to test a specific technique.
                There is no guarantee any technique ever gets ran, it will depend on the board. This is just a maximum.
                Higher will test techniques in more situations but it will also take longer to run.
        """
        if depth > max_depth:
            return
        board.all_normal()
        board.auto_normal()
        if seen is None:
            seen = set()
        key = board.candidates.flatten().tolist()
        i = 0
        for index, value in enumerate(key):
            i |= int(value) << index

        if i in seen:
            return board
        seen.add(i)

        for technique in board.hint():
            print(technique.technique)
            nonlocal technique_applications
            if (
                technique_applications[technique.technique]
                >= max_technique_applications
            ):
                continue
            technique_applications[technique.technique] += 1

            new = copy.deepcopy(board)
            new.apply_action(technique.action)
            new.auto_normal()
            helper(new, max_depth, depth + 1, seen)

    helper(board)
    print(technique_applications)
