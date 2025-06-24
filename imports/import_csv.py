import csv
import sys
from io import StringIO

def parse_csv(file):
    decoded = file.read().decode("utf-8")
    csv_stream = StringIO(decoded)
    original_limit = csv.field_size_limit()
    csv.field_size_limit(sys.maxsize)
    try:
        reader = csv.DictReader(csv_stream)
        rows = list(reader)
        headers = reader.fieldnames
    finally:
        csv.field_size_limit(original_limit)
    return headers, rows
