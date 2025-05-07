import csv
import sys
from io import StringIO

def parse_csv(file):
    decoded = file.read().decode("utf-8")
    csv_stream = StringIO(decoded)
    csv.field_size_limit(sys.maxsize)
    reader = csv.DictReader(csv_stream)
    rows = list(reader)  
    headers = reader.fieldnames
    return headers, rows
