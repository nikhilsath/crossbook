import os
import sys
import sqlite3
import json
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import init_db_path
from db.schema import update_layout, update_field_styling, create_base_table

DB_PATH = 'data/crossbook.db'
init_db_path(DB_PATH)


def fetch_layout(table, field):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            'SELECT col_start, col_span, row_start, row_span FROM field_schema WHERE table_name=? AND field_name=?',
            (table, field),
        ).fetchone()
        return row


def fetch_styling(table, field):
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            'SELECT styling FROM field_schema WHERE table_name=? AND field_name=?',
            (table, field),
        ).fetchone()
        return row[0] if row else None


def test_update_layout_valid_and_invalid_items():
    before = fetch_layout('character', 'race')
    layout = [
        {'field': 'race', 'colStart': 1, 'colSpan': 2, 'rowStart': 3, 'rowSpan': 1},
        {'field': 'character', 'colStart': '2', 'colSpan': 1, 'rowStart': 0, 'rowSpan': 1},
        {'colStart': 1},
        {'field': 'race', 'colStart': 'x', 'colSpan': 1, 'rowStart': 1, 'rowSpan': 1},
    ]
    updated = update_layout('character', layout)
    assert updated == 2
    after = fetch_layout('character', 'race')
    assert after != before

    # reset values
    update_layout('character', [
        {'field': 'race', 'colStart': before[0], 'colSpan': before[1], 'rowStart': before[2], 'rowSpan': before[3]},
        {'field': 'character', 'colStart': 0, 'colSpan': 0, 'rowStart': 0, 'rowSpan': 0},
    ])


def test_update_layout_raises_for_unknown_field():
    with pytest.raises(ValueError):
        update_layout('character', [{'field': 'unknown', 'colStart': 1}])


def test_update_field_styling_success_and_invalid_data():
    before = fetch_styling('character', 'character')
    assert update_field_styling('character', 'character', {'color': 'red'}) is True
    stored = fetch_styling('character', 'character')
    assert stored is not None and 'red' in stored

    with pytest.raises(ValueError):
        update_field_styling('character', 'character', {'bad': {1}})

    update_field_styling('character', 'character', {})
    if before is not None:
        update_field_styling('character', 'character', json.loads(before))


def test_create_base_table_success_and_invalid_names():
    assert create_base_table('1bad', 'Desc', 'title') is False
    assert create_base_table('good_table', 'Desc', 'not valid') is False

    name = 'unit_test_table'
    try:
        assert create_base_table(name, 'Desc', 'title') is True
        with sqlite3.connect(DB_PATH) as conn:
            tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            assert name in tables
    finally:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(f'DROP TABLE IF EXISTS {name}')
            conn.execute('DELETE FROM config_base_tables WHERE table_name=?', (name,))
            conn.execute('DELETE FROM field_schema WHERE table_name=?', (name,))
            conn.commit()

