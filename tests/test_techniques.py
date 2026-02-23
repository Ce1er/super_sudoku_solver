# vim: set foldmethod=marker:
# TODO: think about how is actually best to hide the long techniques arrays, maybe importing from a different file.
from collections.abc import Generator, Callable
import pytest
from human_solver import Technique
from sudoku import Board
import tests.data.test_techniques_data as test_techniques_data
import re
from typing import Optional
import numpy as np
import numpy.typing as npt
import techniques


@pytest.mark.parametrize(
    "board,technique,add_cells,removed_candidates,message_has",
    test_techniques_data.test_technique,
)
class TestTechnique:
    @pytest.fixture
    def null(
        self,
        board: dict[str, npt.NDArray[np.int8 | np.bool]],
        technique: techniques._HumanTechniques,
        add_cells: Optional[list[list[list[int]]]],
        removed_candidates: Optional[list[list[list[list[bool]]]]],
        message_has: list[list[str]],
    ):
        """
        PyTest requires all test functions inside parametrized class to use all params.
        This fixture can be used for tests which do not use all params to supress errors.
        Args:
            message_has: each sublist has regex to match message against
        """
        return

    @pytest.fixture
    def candidates_fixt(self, board) -> npt.NDArray[np.bool]:
        return board["candidates"]

    @pytest.fixture
    def clues_fixt(self, board) -> npt.NDArray[np.int8]:
        return board["clues"]

    @pytest.fixture
    def guesses_fixt(self, board) -> npt.NDArray[np.int8]:
        return board["guesses"]

    @pytest.fixture
    def board_fixt(
        self, candidates_fixt, clues_fixt, guesses_fixt, technique
    ) -> techniques._HumanTechniques:
        return technique(candidates_fixt, clues_fixt, guesses_fixt)

    @pytest.fixture
    def technique_fixt(self, board_fixt):
        techniques = []
        for technique in board_fixt.find():
            techniques.append(technique)
        return techniques

    @pytest.fixture
    def action_fixt(self, technique_fixt):
        actions = []
        for technique_found in technique_fixt:
            actions.append(technique_found.action)
        return actions

    @pytest.fixture
    def num_techniques(self, add_cells):
        return len(add_cells)

    def test_input_data_lengths(self, add_cells, removed_candidates, message_has, null):
        assert (
            len(add_cells) == len(removed_candidates) == len(message_has)
        ), "Test data has parts with different lengths"

    def test_add_cells(self, add_cells, action_fixt, null):
        for action in action_fixt:
            if (cells := action.cells) is None:
                assert None in add_cells
            else:
                assert cells.tolist() in add_cells, f"Invalid add_cells:\n{cells}"

    def test_removed_candidates(self, removed_candidates, action_fixt, null):
        for action in action_fixt:
            if (candidates := action.candidates) is None:
                assert (
                    None in removed_candidates
                ), "Technique did not find any candidates to remove"
            else:
                assert (
                    candidates.tolist() in removed_candidates
                ), "Invalid removed_candidates"

    def test_technique_message(self, technique_fixt, message_has, null):
        # TODO: this is bad. Make message_has specific to each application of a technique instead of checking whole list.
        correct = False
        for technique in technique_fixt:
            for message in message_has:
                for part in message:
                    if re.match(part, technique.message) is not None:
                        break
                else:
                    correct = True
                    break

        assert correct is True, "Message does not contain all required parts"

    def test_unique_messages(self, technique_fixt, null):
        seen: set[str] = set()
        count = 0
        for technique in technique_fixt:
            seen.add(technique.message)
            count += 1

        assert len(seen) == count, "Some messages are duplicates"

    def test_num_found(self, technique_fixt, num_techniques, null):
        count = 0
        for technique in technique_fixt:
            count += 1

        assert count == num_techniques
