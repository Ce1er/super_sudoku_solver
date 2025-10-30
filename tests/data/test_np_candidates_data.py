import pytest
import numpy as np

_test_adjacent = [
    {
        "name": "Single coord::ndim=2",
        "coords": np.array([[3, 3]]),
        "adjacent_row": np.array(
            [
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [True, True, True, True, True, True, True, True, True],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
            ]
        ),
        "adjacent_column": np.array(
            [
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
            ]
        ),
        "adjacent_box": np.array(
            [
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, True, True, True, False, False, False],
                [False, False, False, True, True, True, False, False, False],
                [False, False, False, True, True, True, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
            ]
        ),
        "adjacent": np.array(
            [
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [True, True, True, True, True, True, True, True, True],
                [False, False, False, True, True, True, False, False, False],
                [False, False, False, True, True, True, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
            ]
        ),
    },
    {
        "name": "Single coord::ndim=1",
        "coords": np.array([3, 3]),
        "adjacent_row": np.array(
            [
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [True, True, True, True, True, True, True, True, True],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
            ]
        ),
        "adjacent_column": np.array(
            [
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
            ]
        ),
        "adjacent_box": np.array(
            [
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, True, True, True, False, False, False],
                [False, False, False, True, True, True, False, False, False],
                [False, False, False, True, True, True, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
            ]
        ),
        "adjacent": np.array(
            [
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [True, True, True, True, True, True, True, True, True],
                [False, False, False, True, True, True, False, False, False],
                [False, False, False, True, True, True, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
                [False, False, False, True, False, False, False, False, False],
            ]
        ),
    },
    {
        "name": "Multiple coords::ndim=2",
        "coords": np.array([[0, 0], [8, 8], [0, 2]]),
        "adjacent_row": np.array(
            [
                [True, True, True, True, True, True, True, True, True],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [True, True, True, True, True, True, True, True, True],
            ]
        ),
        "adjacent_column": np.array(
            [
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
            ]
        ),
        "adjacent_box": np.array(
            [
                [True, True, True, False, False, False, False, False, False],
                [True, True, True, False, False, False, False, False, False],
                [True, True, True, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, True, True, True],
                [False, False, False, False, False, False, True, True, True],
                [False, False, False, False, False, False, True, True, True],
            ]
        ),
        "adjacent": np.array(
            [
                [True, True, True, True, True, True, True, True, True],
                [True, True, True, False, False, False, False, False, True],
                [True, True, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, True, True, True],
                [True, False, True, False, False, False, True, True, True],
                [True, True, True, True, True, True, True, True, True],
            ]
        ),
    },
    {
        "name": "Multiple coords::ndim=3",
        "coords": np.array([[[0, 0], [8, 8], [0, 2]]]),
        "adjacent_row": np.array(
            [
                [True, True, True, True, True, True, True, True, True],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [True, True, True, True, True, True, True, True, True],
            ]
        ),
        "adjacent_column": np.array(
            [
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
            ]
        ),
        "adjacent_box": np.array(
            [
                [True, True, True, False, False, False, False, False, False],
                [True, True, True, False, False, False, False, False, False],
                [True, True, True, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, False, False, False],
                [False, False, False, False, False, False, True, True, True],
                [False, False, False, False, False, False, True, True, True],
                [False, False, False, False, False, False, True, True, True],
            ]
        ),
        "adjacent": np.array(
            [
                [True, True, True, True, True, True, True, True, True],
                [True, True, True, False, False, False, False, False, True],
                [True, True, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, False, False, True],
                [True, False, True, False, False, False, True, True, True],
                [True, False, True, False, False, False, True, True, True],
                [True, True, True, True, True, True, True, True, True],
            ]
        ),
    },
]

test_adjacent = []

for case in _test_adjacent:
    test_adjacent.append(
        pytest.param(
            case["coords"],
            case["adjacent_row"],
            case["adjacent_column"],
            case["adjacent_box"],
            case["adjacent"],
            id=case["name"],
        )
    )
