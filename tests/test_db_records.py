import os
import sqlite3
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import init_db_path
from db.records import (
    create_record,
    delete_record,
    count_nonnull,
    field_distribution,
    get_record_by_id,
)
from db.edit_fields import (
    add_column_to_table,
    drop_column_from_table,
    add_field_to_schema,
    remove_field_from_schema,
)

DB_PATH = 'data/crossbook.db'
init_db_path(DB_PATH)


def column_names(table):
    with sqlite3.connect(DB_PATH) as conn:
        return [r[1] for r in conn.execute(f"PRAGMA table_info('{table}')").fetchall()]


def test_create_delete_and_counts():
    baseline = count_nonnull('location', 'location')
    dist_before = field_distribution('location', 'location')

    data = {
        'location': 'UnitTestPlace',
        'description': '<p>Hi</p><script>bad()</script>',
    }
    rec_id = create_record('location', data)
    assert isinstance(rec_id, int)

    rec = get_record_by_id('location', rec_id)
    assert rec['location'] == 'UnitTestPlace'
    assert '<script>' not in rec['description']

    assert count_nonnull('location', 'location') == baseline + 1
    dist_mid = field_distribution('location', 'location')
    assert dist_mid.get('UnitTestPlace') == 1

    assert delete_record('location', rec_id) is True
    assert count_nonnull('location', 'location') == baseline
    dist_after = field_distribution('location', 'location')
    assert 'UnitTestPlace' not in dist_after


def test_add_and_drop_column():
    col = 'temp_testcol'
    if col in column_names('character'):
        drop_column_from_table('character', col)
        remove_field_from_schema('character', col)
    add_column_to_table('character', col, 'text')
    add_field_to_schema('character', col, 'text')
    assert col in column_names('character')

    drop_column_from_table('character', col)
    remove_field_from_schema('character', col)
    assert col not in column_names('character')
