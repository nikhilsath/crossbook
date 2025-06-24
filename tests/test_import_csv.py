import os
import sys
import io
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from imports.import_csv import parse_csv
import csv


def test_parse_csv_decodes_and_parses_rows():
    sample = b"col1,col2\nA,1\nB,2\n"
    original_limit = csv.field_size_limit()
    headers, rows = parse_csv(io.BytesIO(sample))
    assert headers == ["col1", "col2"]
    assert rows == [{"col1": "A", "col2": "1"}, {"col1": "B", "col2": "2"}]
    assert csv.field_size_limit() == original_limit


