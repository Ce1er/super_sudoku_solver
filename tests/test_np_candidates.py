import pytest
import tests.data.test_np_candidates_data as test_np_candidates_data
import np_candidates
import numpy as np


@pytest.mark.parametrize(
    "coords,adjacent_row,adjacent_column,adjacent_box,adjacent",
    test_np_candidates_data.test_adjacent,
)
class TestAdjacent:
    @pytest.fixture
    def null(self, coords, adjacent_row, adjacent_column, adjacent_box, adjacent):
        return

    def test_valid_input(
        self, coords, adjacent_row, adjacent_column, adjacent_box, adjacent
    ):
        print(coords.dtype)
        # assert coords.dtype == np.integer, "Invalid coords dtype" # Exact type of integer doesn't matter but this is a direct check to abc np.integer. Check if subclass instead
        assert adjacent_row.shape == (9, 9), "Invalid adjacent_row shape"
        assert adjacent_column.shape == (9, 9), "Invalid adjacent_column shape"
        assert adjacent_box.shape == (9, 9), "Invalid adjacent_box shape"
        assert adjacent.shape == (9, 9), "Invalid adjacent shape"
        assert adjacent_row.dtype == np.bool, "Invalid adjacent_row dtype"
        assert adjacent_column.dtype == np.bool, "Invalid adjacent_column dtype"
        assert adjacent_box.dtype == np.bool, "Invalid adjacent_box dtype"
        assert adjacent.dtype == np.bool, "Invalid adjacent dtype"

    def test_adjacent_row(self, coords, adjacent_row, null):
        assert (
            np_candidates.adjacent_row(coords).tolist() == adjacent_row.tolist()
        ), "adjacent_row returned wrong array"

    def test_adjacent_column(self, coords, adjacent_column, null):
        assert (
            np_candidates.adjacent_column(coords).tolist() == adjacent_column.tolist()
        ), "adjacent_column returned wrong array"

    def test_adjacent_box(self, coords, adjacent_box, null):
        assert (
            np_candidates.adjacent_box(coords).tolist() == adjacent_box.tolist()
        ), "adjacent_box returned wrong array"

    def test_adjacent(self, coords, adjacent, null):
        assert (
            np_candidates.adjacent(coords).tolist() == adjacent.tolist()
        ), "adjacent returned wrong array"
