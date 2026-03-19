import os
import sys
import csv
from functools import partial
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.validation import (
    validate_text_column,
    validate_textarea_column,
    validate_number_column,
    validate_boolean_column,
    validate_select_column,
    validate_multi_select_column,
)


def test_validate_text_column_counts():
    values = [
        "",  # blank
        "normal",  # valid
        "# heading",  # markdown warning
        "<p>html</p>",  # html warning
        '{"key": 1}',  # json warning
        "x" * 1001,  # over-length invalid
    ]
    result = validate_text_column(values)
    assert result["blank"] == 1
    assert result["valid"] == 4
    assert result["invalid"] == 1
    assert result["warning"] == 3


def test_validate_textarea_column_edge_cases():
    long_text = "x" * (csv.field_size_limit() + 1)
    values = [
        "",  # blank
        "short text",  # valid
        '{"a":1}',  # valid but warning
        long_text,  # invalid
    ]
    result = validate_textarea_column(values)
    assert result["blank"] == 1
    assert result["valid"] == 2
    assert result["invalid"] == 1
    assert result["warning"] == 1


@pytest.mark.parametrize(
    "validator,values,expected",
    [
        (
            validate_number_column,
            ["", "10", "3.14", "notnum", "8e5"],
            {"blank": 1, "valid": 3, "invalid": 1},
        ),
        (
            partial(validate_number_column, integer_only=True),
            ["1", "2.5", "abc", ""],
            {"blank": 1, "valid": 1, "invalid": 2},
        ),
        (
            validate_boolean_column,
            ["true", "False", "yes", "no", "1", "0", "", "maybe"],
            {"blank": 1, "valid": 6, "invalid": 1},
        ),
        (
            lambda v: validate_select_column(v, ["Apple", "Banana", "Cherry"]),
            ["apple", "", "Durian", "BANANA"],
            {"blank": 1, "valid": 2, "invalid": 1},
        ),
    ],
)
def test_column_validators_counts(validator, values, expected):
    result = validator(values)
    assert result["blank"] == expected["blank"]
    assert result["valid"] == expected["valid"]
    assert result["invalid"] == expected["invalid"]


def test_validate_multi_select_column_counts():
    options = ["red", "green", "blue"]
    values = ["", "red, BLUE", "green, yellow", "red , green", "Blue, Pink"]
    result = validate_multi_select_column(values, options)
    assert result["blank"] == 1
    assert result["valid"] == 2
    assert result["invalid"] == 2
    assert result["warning"] == 0

