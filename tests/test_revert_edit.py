import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.records import revert_edit


def test_revert_edit_returns_false_for_none_field():
    entry = {
        'table_name': 'character',
        'record_id': 1,
        'field_name': None,
        'old_value': None,
        'new_value': None,
    }
    assert revert_edit(entry) is False

