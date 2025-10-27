# vim: set foldmethod=marker:
# TODO: think about how is actually best to hide the long techniques arrays, maybe importing from a different file. 
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


# def test_naked_single(board):
#     techniques = [
#         # {{{
#         Technique(
#             "Naked Single",
#             [
#                 np.array([1, 7]),
#                 "is",
#                 np.array([[5]]),
#                 "because it is the only candidate for the cell.",
#             ],
#         ),
#         Technique(
#             "Naked Single",
#             [
#                 np.array([6, 6]),
#                 "is",
#                 np.array([[5]]),
#                 "because it is the only candidate for the cell.",
#             ],
#         ),
#         Technique(
#             "Naked Single",
#             [
#                 np.array([7, 6]),
#                 "is",
#                 np.array([[7]]),
#                 "because it is the only candidate for the cell.",
#             ],
#         ),
#         # }}}
#     ]
#     # TODO: check those are all correct and the only valid naked singles. I'm just assuming my current implementation works currently.
#     for technique in board._naked_singles():
#         if technique in techniques:
#             continue
#         else:
#             raise Exception  # TODO: check how actually to do this
#
#
# def test_hidden_single(board):
#     techniques = [
#         ### {{{
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (4, 3) is 1 because there are no other 1s in the column",
#         ).add_cell(np.array([0, 3, 2])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (4, 3) is 1 because there are no other 1s in the box",
#         ).add_cell(np.array([0, 3, 2])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (6, 8) is 1 because there are no other 1s in the row",
#         ).add_cell(np.array([0, 5, 7])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (7, 4) is 2 because there are no other 2s in the row",
#         ).add_cell(np.array([1, 6, 3])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (7, 4) is 2 because there are no other 2s in the box",
#         ).add_cell(np.array([1, 6, 3])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (8, 5) is 4 because there are no other 4s in the row",
#         ).add_cell(np.array([3, 7, 4])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (8, 5) is 4 because there are no other 4s in the box",
#         ).add_cell(np.array([3, 7, 4])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (1, 7) is 5 because there are no other 5s in the column",
#         ).add_cell(np.array([4, 0, 6])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (1, 7) is 5 because there are no other 5s in the box",
#         ).add_cell(np.array([4, 0, 6])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (3, 6) is 7 because there are no other 7s in the row",
#         ).add_cell(np.array([6, 2, 5])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (3, 6) is 7 because there are no other 7s in the box",
#         ).add_cell(np.array([6, 2, 5])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (2, 9) is 8 because there are no other 8s in the row",
#         ).add_cell(np.array([7, 1, 8])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (2, 9) is 8 because there are no other 8s in the box",
#         ).add_cell(np.array([7, 1, 8])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (4, 5) is 8 because there are no other 8s in the row",
#         ).add_cell(np.array([7, 3, 4])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (4, 5) is 8 because there are no other 8s in the column",
#         ).add_cell(np.array([7, 3, 4])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (4, 5) is 8 because there are no other 8s in the box",
#         ).add_cell(np.array([7, 3, 4])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (8, 7) is 8 because there are no other 8s in the column",
#         ).add_cell(np.array([7, 7, 6])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (1, 4) is 9 because there are no other 9s in the column",
#         ).add_cell(np.array([8, 0, 3])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (1, 4) is 9 because there are no other 9s in the box",
#         ).add_cell(np.array([8, 0, 3])),
#         Technique(
#             "Hidden Single",  # It could be a naked single but _naked_singles() should be ran first
#             "Cell (4, 8) is 9 because there are no other 9s in the column",
#         ).add_cell(np.array([8, 3, 7])),
#         ### }}}
#     ]  # TODO: check those are all correct
#     for technique in board._hidden_singles():
#         if technique in techniques:
#             continue
#         else:
#             raise Exception
#         # TODO: this will be pretty similar for testing all the methods so work out how to decrease repetitive tests
