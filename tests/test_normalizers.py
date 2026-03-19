import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.normalizers import normalize_boolean, normalize_number, normalize_multi


@pytest.mark.parametrize("value,expected", [
    ("1", "1"),
    ("true", "1"),
    ("True", "1"),
    ("on", "1"),
    ("yes", "1"),
    ("0", "0"),
    ("false", "0"),
    ("no", "0"),
    ("maybe", "0"),
    ("", "0"),
])
def test_normalize_boolean(value, expected):
    assert normalize_boolean(value) == expected


@pytest.mark.parametrize("value,expected", [
    ("3.14", "3.14"),
    ("10", "10.0"),
    ("-5", "-5.0"),
    ("0", "0.0"),
])
def test_normalize_number_valid(value, expected):
    assert normalize_number(value) == expected


def test_normalize_number_invalid():
    assert normalize_number("notanumber") == "0"
    assert normalize_number(None) == "0"


@pytest.mark.parametrize("value,expected", [
    (["a", "b", "c"], "a, b, c"),
    (("x", "y"), "x, y"),
    ({"p", "q"}, None),  # set order undefined; check it contains both
    (None, ""),
    ("already a string", "already a string"),
    (42, "42"),
])
def test_normalize_multi(value, expected):
    result = normalize_multi(value)
    if expected is None:
        # set: just verify both elements present
        assert "p" in result and "q" in result
    else:
        assert result == expected
