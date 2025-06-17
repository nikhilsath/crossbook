import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import check_db_status

DB_PATH = 'data/crossbook.db'


def test_check_db_status_valid_missing_corrupted():
    assert check_db_status(DB_PATH) == 'valid'
    assert check_db_status('nonexistent.db') == 'missing'
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b'not a database')
        corrupt_path = tmp.name
    try:
        assert check_db_status(corrupt_path) == 'corrupted'
    finally:
        os.remove(corrupt_path)

