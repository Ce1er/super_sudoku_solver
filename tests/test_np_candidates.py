import pytest
import tests.data.test_np_candidates_data as test_np_candidates_data
import np_candidates
import numpy as np


@pytest.mark.parametrize(
    "coords,to_n,strict,any_adjacency,adjacent_row,adjacent_column,adjacent_box,adjacent",
    test_np_candidates_data.test_adjacent,
)
class TestAdjacent:
    @pytest.fixture
    def null(
        self,
        coords,
        to_n,
        strict,
        any_adjacency,
        adjacent_row,
        adjacent_column,
        adjacent_box,
        adjacent,
    ):
        return

    def test_valid_input(
        self,
        coords,
        to_n,
        strict,
        any_adjacency,
        adjacent_row,
        adjacent_column,
        adjacent_box,
        adjacent,
    ):
        # assert coords.dtype == np.integer, "Invalid coords dtype" # Exact type of integer doesn't matter but this is a direct check to abc np.integer. Check if subclass instead
        assert type(coords) is np.ndarray, "Invalid coords type"
        assert adjacent_row.shape == (9, 9), "Invalid adjacent_row shape"
        assert adjacent_column.shape == (9, 9), "Invalid adjacent_column shape"
        assert adjacent_box.shape == (9, 9), "Invalid adjacent_box shape"
        assert adjacent.shape == (9, 9), "Invalid adjacent shape"
        assert adjacent_row.dtype == np.bool, "Invalid adjacent_row dtype"
        assert adjacent_column.dtype == np.bool, "Invalid adjacent_column dtype"
        assert adjacent_box.dtype == np.bool, "Invalid adjacent_box dtype"
        assert adjacent.dtype == np.bool, "Invalid adjacent dtype"
        assert type(to_n) is int, "Invalid to_n type"
        assert type(strict) is bool, "Invalid strict type"
        assert type(any_adjacency) is bool, "Invalid any_adjacency type"

    @pytest.fixture
    def normal_args(self, coords, to_n, strict):
        return (coords, to_n, strict)

    @pytest.fixture
    def adjacency_args(self, coords, to_n, strict, any_adjacency):
        return (coords, to_n, strict, any_adjacency)

    def test_adjacent_row(self, normal_args, adjacent_row, null):
        assert (
            np_candidates.adjacent_row(*normal_args).tolist() == adjacent_row.tolist()
        ), "adjacent_row returned wrong array"

    def test_adjacent_column(self, normal_args, adjacent_column, null):
        assert (
            np_candidates.adjacent_column(*normal_args).tolist()
            == adjacent_column.tolist()
        ), "adjacent_column returned wrong array"

    def test_adjacent_box(self, normal_args, adjacent_box, null):
        print(*normal_args)
        assert (
            np_candidates.adjacent_box(*normal_args).tolist() == adjacent_box.tolist()
        ), "adjacent_box returned wrong array"

    def test_adjacent(self, adjacency_args, adjacent, null):
        assert (
            np_candidates.adjacent(*adjacency_args).tolist() == adjacent.tolist()
        ), "adjacent returned wrong array"
