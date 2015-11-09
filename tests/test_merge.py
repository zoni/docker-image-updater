import pytest
from diu.merge import merge


def test_shallow_dict_merge():
    a = {
        'one': [1, 2, 3]
    }
    b = {
        'two': [2, 3, 4]
    }

    expected = {
        'one': [1, 2, 3],
        'two': [2, 3, 4],
    }
    assert merge(a, b) == expected

    a = {
        'one': [1, 2, 3]
    }
    b = {}

    expected = {
        'one': [1, 2, 3],
    }
    assert merge(a, b) == expected


def test_deep_dict_merge():
    a = {
        'one': [1, 2, 3],
        'three': {'one': 1},
    }
    b = {
        'two': [2, 3, 4],
        'three': {'two': 2},
    }

    expected = {
        'one': [1, 2, 3],
        'two': [2, 3, 4],
        'three': {
            'one': 1,
            'two': 2,
        },
    }
    assert merge(a, b) == expected


def test_list_within_dict_merge():
    a = {
        'one': [1, 2],
    }
    b = {
        'one': [2, 3],
    }

    expected = {
        'one': [1, 2, 3],
    }
    assert merge(a, b) == expected


def test_list_merge():
    a = [1, 2]
    b = [2, 3]
    expected = [1, 2, 3]
    assert merge(a, b) == expected

    a = [1, 2]
    b = []
    expected = [1, 2]
    assert merge(a, b) == expected


def test_str_merge():
    a = "some"
    b = "string"
    assert merge(a, b) == b


def test_int_merge():
    a = 1
    b = 2
    assert merge(a, b) == b


def test_different_types_merge():
    a = {}
    b = [1]
    with pytest.raises(ValueError):
        assert merge(a, b)
