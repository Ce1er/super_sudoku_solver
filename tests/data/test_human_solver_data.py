# vim: foldmethod=marker
from _pytest.mark import ParameterSet
from human_solver import Technique, Human_Solver
from collections.abc import Generator, Callable
from typing import Optional
import pytest
from sudoku import Board
import numpy as np

board_1 = Human_Solver(
    Board(
        ".18....7..7...19...6.85.12.6..7..3..7..51..8.8.4..97.5.47.98.5...26.5.3...6...24."
    )
)
board_1.auto_normal()

board_2 = Human_Solver(
    Board(
        ".....2...71.95.....86.34..997542.......573.9..3..91574...2476383...15927.273.9..."
    )
)
board_2.auto_normal()

remove_candidates = np.full((9, 9, 9), False, dtype=np.bool)

remove_candidates[5, 0, 3] = True

board_2.remove_candidates(remove_candidates)


boards: dict[int, Human_Solver] = {1: board_1, 2: board_2}


test_technique: list[ParameterSet] = []

naked_singles_board_1 = {
    "name": "Naked Singles::Board 1",
    "func": Human_Solver._naked_singles,
    "board": boards[1],
    "cases": [
        # Cases {{{
        {
            "add_cells":
            # 6 at r2c8
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1,  5, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(2, 8\)", "number 6"],
        },
        {
            "add_cells":
            # 6 at r7c7
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1,  5, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: off
            "removed_candidates":
            None,
            "message_has":
            [r"\(7, 7\)", "number 6"]
        },
        {
            "add_cells":
            # 8 at r8c7
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, 7, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(8, 7\)", "number 8"],
        },
        # }}}
    ],
}

hidden_singles_board_1 = {
    "name": "Hidden Singles::Board 1",
    "func": Human_Solver._hidden_singles,
    "board": boards[1],
    "cases": [
        # Cases {{{
        {
            "add_cells":
            # 1 at r4c3 because column
            # fmt: off
         [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
          [-1, -1, -1, -1, -1, -1, -1, -1, -1],
          [-1, -1, -1, -1, -1, -1, -1, -1, -1],
          [-1, -1,  0, -1, -1, -1, -1, -1, -1],
          [-1, -1, -1, -1, -1, -1, -1, -1, -1],
          [-1, -1, -1, -1, -1, -1, -1, -1, -1],
          [-1, -1, -1, -1, -1, -1, -1, -1, -1],
          [-1, -1, -1, -1, -1, -1, -1, -1, -1],
          [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(4, 3\)", "number 1", "column"],
        },
        {
            "add_cells":
            # 1 at r4c3 because box
            # fmt: off
        [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1,  0, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(4, 3\)", "number 1", "box"],
        },
        {
            "add_cells":
            # 1 at r6c8 because row
            # fmt: off
        [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1,  0, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1],
         [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(6, 8\)", "number 1", "row"],
        },
        {
            "add_cells":
            # 2 at r7c4 because row
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1,  1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(7, 4\)", "number 2", "row"],
        },
        {
            "add_cells":
            # 2 at r7c4 because box
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1,  1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(7, 4\)", "number 2", "box"],
        },
        {
            "add_cells":
            # 4 at r8c5 because row
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1,  3, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(8, 5\)", "number 4", "row"],
        },
        {
            "add_cells":
            # 4 at r8c5 because box
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1,  3, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(8, 5\)", "number 4", "box"],
        },
        {
            "add_cells":
            # 5 at r1c7 because column
            # fmt: off
            [[-1, -1, -1, -1, -1, -1,  4, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(1, 7\)", "number 5", "column"],
        },
        {
            "add_cells":
            # 5 at r1c7 because box
            # fmt: off
            [[-1, -1, -1, -1, -1, -1,  4, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(1, 7\)", "number 5", "box"],
        },
        {
            "add_cells":
            # 7 at r3c6 because row
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1,  6, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(3, 6\)", "number 7", "row"],
        },
        {
            "add_cells":
            # 7 at r3c6 because box
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1,  6, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(3, 6\)", "number 7", "box"],
        },
        {
            "add_cells":
            # 8 at r2c9 because row
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1,  7],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(2, 9\)", "number 8", "row"],
        },
        {
            "add_cells":
            # 8 at r2c9 because box
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1,  7],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(2, 9\)", "number 8", "box"],
        },
        {
            "add_cells":
            # 8 at r4c5 because row
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1,  7, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(4, 5\)", "number 8", "row"],
        },
        {
            "add_cells":
            # 8 at r4c5 because column
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1,  7, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(4, 5\)", "number 8", "column"],
        },
        {
            "add_cells":
            # 8 at r4c5 because box
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1,  7, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(4, 5\)", "number 8", "box"],
        },
        {
            "add_cells":
            # 9 at r1c4 because column
            # fmt: off
            [[-1, -1, -1,  8, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(1, 4\)", "number 9", "column"],
        },
        {
            "add_cells":
            # 9 at r1c4 because box
            # fmt: off
            [[-1, -1, -1,  8, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(1, 4\)", "number 9", "box"],
        },
        {
            "add_cells":
            # 9 at r4c8 because column
            # fmt: off
            [[-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1,  8, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1],
             [-1, -1, -1, -1, -1, -1, -1, -1, -1]],
            # fmt: on
            "removed_candidates": None,
            "message_has": [r"\(4, 8\)", "number9", " column"],
        },
        # }}}
    ],
}

naked_pairs_board_1 = {
    "name": "Naked Pairs::Board 1",
    "func": Human_Solver._naked_pairs,
    "board": boards[1],
    "cases": [
        # Cases {{{
        {
            # r3c3 and r5c3 are 3 and 9
            "add_cells": None,
            "removed_candidates": [
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, True, False, False, False, False, False, False],
                    [False, False, True, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, True, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, True, False, False, False, False, False, False],
                    [False, False, True, False, False, False, False, False, False],
                    [False, False, True, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
            ],
            "message_has": [r"\(3, 3\)", r"\(5, 3\)", "3", "9", "column"],
        },
        {
            # r6c2 and r6c4 are 2 and 3
            "add_cells": None,
            "removed_candidates": [
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, True, False, True, True, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, True, False, True, True, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
            ],
            "message_has": [r"\(6, 2\)", r"\(6, 4\)", "2", "3", "row"],
        },
        {
            # r9c5 and r9c6 are 3 and 7
            "add_cells": None,
            "removed_candidates": [
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, True, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [True, True, False, True, True, True, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, True, False, False, False, False],
                    [False, False, False, False, True, True, False, False, True],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
            ],
            "message_has": [r"\(9, 5\)", r"\(9, 6\)", "3", "7", "row", "box"],
        },
        # }}}
    ],
}

skyscrapers_board_2 = {
    "name": "Skyscrapers::Board 2",
    "func": Human_Solver._skyscraper,
    "board": boards[2],
    "cases": [
        # Cases {{{
        {
            "add_cells": None,
            "removed_candidates":
            # num 6 cannot be at r6c1
            [
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [True, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
            ],
            "message_has": [
                r"(5, 2)",
                r"(6, 4)",
                "only 6 in their column",
                r"(8, 2)",
                r"(8, 4)",
                "share a row",
            ],
        },
        {
            "add_cells": None,
            "removed_candidates":
            # num 6 can't be at r9c1 or r5c2
            [
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, True, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [True, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
                [
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                    [False, False, False, False, False, False, False, False, False],
                ],
            ],
            "message_has": [
                r"(6, 1)",
                r"(8, 2)",
                "only 6 in their row",
                r"(6, 4)",
                r"(8, 4)",
                "share a column",
            ],
        },
        # }}}
    ],
}

tests = [
    naked_singles_board_1,
    hidden_singles_board_1,
    naked_pairs_board_1,
    skyscrapers_board_2,
]

for test in tests:
    add_cells = []
    removed_candidates = []
    message_has = []

    for case in test["cases"]:
        add_cells.append(case["add_cells"])
        removed_candidates.append(case["removed_candidates"])
        message_has.append("message_has")

    test_technique.append(
        pytest.param(
            test["board"],
            test["func"],
            add_cells,
            removed_candidates,
            message_has,
            id=test["name"],
        )
    )
