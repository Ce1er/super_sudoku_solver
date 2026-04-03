# # import line_profiler
# import copy
# import pytest
# from sudoku import Board
# # from human_solver import HumanSolver
# from techniques import TECHNIQUES
#
# from tests.data.test_techniques_data import board_1
#
# @pytest.fixture
# def board():
#     return board_1
#
# # @line_profiler.profile
# def apply_all_techniques(board, max_depth=5, depth=0, seen=None):
#     if depth > max_depth:
#         return
#     board.auto_normal()
#     if seen is None:
#         seen = set()
#     key = board.get_candidates().flatten().tolist()
#     i = 0
#     for index, value in enumerate(key):
#         i |= int(value) << index
#
#     if i in seen:
#         return board
#     seen.add(i)
#
#     for technique in board.hint():
#         # print(technique.message)
#         new = copy.deepcopy(board)
#         new.apply_action(technique.get_action())
#         new.auto_normal()
#         if not new.is_valid():
#             print(new.cells)
#             raise AssertionError(
#                 f"Technique {technique.get_technique()} produced invalid board."
#             )
#
#         if (
#             board.get_candidates().tobytes() == new.get_candidates().tobytes()
#             and board.cells.tobytes() == new.cells.tobytes()
#         ):
#             raise AssertionError(
#                 f"Technique {technique.get_technique()} did not change any candidates"
#             )
#
#         apply_all_techniques(new, max_depth, depth + 1, seen)
#         break
#
#
# def test_human_techniques(board):
#     apply_all_techniques(board)

# TODO: Make this work with new setup
