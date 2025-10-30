# vim: set foldmethod=marker:
# TODO: think about how is actually best to hide the long techniques arrays, maybe importing from a different file.
from collections.abc import Generator, Callable
import pytest
from human_solver import HumanSolver, Technique
from sudoku import Board
import tests.data.test_human_solver_data as test_human_solver_data
import re
from typing import Optional


@pytest.mark.parametrize(
    "board,technique,add_cells,removed_candidates,message_has",
    test_human_solver_data.test_technique,
)
class TestTechnique:
    @pytest.fixture
    def null(
        self,
        board: HumanSolver,
        technique: Callable[[HumanSolver], Generator[Technique]],
        add_cells: Optional[list[list[list[int]]]],
        removed_candidates: Optional[list[list[list[list[bool]]]]],
        message_has: list[list[str]],
    ):
        """
        PyTest requires all test functions inside parametrized class to use all params.
        This should be used for tests which do not use all params to suppress errors.
        """
        return

    @pytest.fixture
    def board_fixt(self, board) -> HumanSolver:
        # new = HumanSolver(Board(board))
        # new.auto_normal()
        # return new
        return board

    @pytest.fixture
    def technique_fixt(self, board_fixt, technique):
        techniques = []
        assert (
            technique(board_fixt) is not None
        ), f"{technique} does not yield any Techniques"
        for technique_found in technique(board_fixt):
            techniques.append(technique_found)
        return techniques

    @pytest.fixture
    def action_fixt(self, technique_fixt):
        actions = []
        for technique_found in technique_fixt:
            actions.append(technique_found.get_action())
        return actions

    @pytest.fixture
    def num_techniques(self, add_cells):
        return len(add_cells)

    def test_valid_input(self, add_cells, removed_candidates, message_has, null):
        assert (
            len(add_cells) == len(removed_candidates) == len(message_has)
        ), "Test data has parts with different lengths"

    def test_add_cells(self, add_cells, action_fixt, null):
        for action in action_fixt:
            if (cells := action.get_cells()) is None:
                assert None in add_cells
            else:
                assert cells.tolist() in add_cells, f"Invalid add_cells:\n{cells}"

    def test_removed_candidates(self, removed_candidates, action_fixt, null):
        for action in action_fixt:
            if (candidates := action.get_candidates()) is None:
                assert (
                    None in removed_candidates
                ), "Technique did not find any candidates to remove"
            else:
                assert (
                    candidates.tolist() in removed_candidates
                ), "Invalid removed_candidates"

    def test_technique_message(self, technique_fixt, message_has, null):
        correct = False
        for technique in technique_fixt:
            for message in message_has:
                for part in message:
                    if re.match(part, technique.get_message()) is not None:
                        break
                else:
                    correct = True
                    break

        assert correct is True, "Message does not contain all required parts"

    def test_unique_messages(self, technique_fixt, null):
        seen: set[str] = set()
        count = 0
        for technique in technique_fixt:
            seen.add(technique.get_message())
            count += 1

        assert len(seen) == count, "Some messages are duplicates"

    def test_num_found(self, technique_fixt, num_techniques, null):
        count = 0
        for technique in technique_fixt:
            count += 1

        assert count == num_techniques
