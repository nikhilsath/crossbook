import csv

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


def test_validate_number_column_default_and_integer_only():
    values = ["", "10", "3.14", "notnum", "8e5"]
    res = validate_number_column(values)
    assert res["blank"] == 1
    assert res["valid"] == 3
    assert res["invalid"] == 1

    int_values = ["1", "2.5", "abc", ""]
    res_int = validate_number_column(int_values, integer_only=True)
    assert res_int["blank"] == 1
    assert res_int["valid"] == 1
    assert res_int["invalid"] == 2


def test_validate_boolean_column_counts():
    values = ["true", "False", "yes", "no", "1", "0", "", "maybe"]
    result = validate_boolean_column(values)
    assert result["blank"] == 1
    assert result["valid"] == 6
    assert result["invalid"] == 1


def test_validate_select_column_counts():
    options = ["Apple", "Banana", "Cherry"]
    values = ["apple", "", "Durian", "BANANA"]
    result = validate_select_column(values, options)
    assert result["blank"] == 1
    assert result["valid"] == 2
    assert result["invalid"] == 1


def test_validate_multi_select_column_counts():
    options = ["red", "green", "blue"]
    values = ["", "red, BLUE", "green, yellow", "red , green", "Blue, Pink"]
    result = validate_multi_select_column(values, options)
    assert result["blank"] == 1
    assert result["valid"] == 2
    assert result["invalid"] == 2
    assert result["warning"] == 0

