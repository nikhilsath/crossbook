import csv
from io import StringIO

def parse_csv(file):
    decoded = file.read().decode("utf-8")
    csv_stream = StringIO(decoded)
    reader = csv.DictReader(csv_stream)
    rows = list(reader)  
    headers = reader.fieldnames
    return headers, rows
