import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from db.edit_history import revert_edit
from db.database import init_db_path

init_db_path('data/crossbook.db')
DB_PATH = 'data/crossbook.db'


def test_revert_edit_returns_false_for_none_field():
    entry = {
        'table_name': 'character',
        'record_id': 1,
        'field_name': None,
        'old_value': None,
        'new_value': None,
    }
    assert revert_edit(entry) is False


def test_revert_edit_restores_value_and_logs_entry():
    with sqlite3.connect(DB_PATH) as conn:
        original = conn.execute(
            'SELECT character FROM character WHERE id = 1'
        ).fetchone()[0]
        conn.execute(
            'UPDATE character SET character = ? WHERE id = 1',
            ('TempName',),
        )
        max_id = conn.execute(
            'SELECT COALESCE(MAX(id),0) FROM edit_history'
        ).fetchone()[0]
        conn.commit()

    entry = {
        'table_name': 'character',
        'record_id': 1,
        'field_name': 'character',
        'old_value': original,
        'new_value': 'TempName',
    }
    assert revert_edit(entry)

    with sqlite3.connect(DB_PATH) as conn:
        value = conn.execute(
            'SELECT character FROM character WHERE id = 1'
        ).fetchone()[0]
        assert value == original
        rows = conn.execute(
            'SELECT field_name, old_value, new_value, actor FROM edit_history '
            'WHERE id > ? ORDER BY id',
            (max_id,),
        ).fetchall()
        assert len(rows) == 1
        assert rows[0] == ('character', 'TempName', original, 'undo')
        conn.execute('DELETE FROM edit_history WHERE id > ?', (max_id,))
        conn.commit()


def test_revert_edit_adds_and_removes_relationships():
    with sqlite3.connect(DB_PATH) as conn:
        # ensure no existing relationship
        conn.execute(
            "DELETE FROM relationships WHERE table_a='character' AND id_a=1 AND table_b='location' AND id_b=1"
        )
        max_id = conn.execute(
            'SELECT COALESCE(MAX(id),0) FROM edit_history'
        ).fetchone()[0]
        conn.commit()

    add_entry = {
        'table_name': 'character',
        'record_id': 1,
        'field_name': 'relation_location',
        'old_value': None,
        'new_value': '1',
    }
    assert revert_edit(add_entry)

    with sqlite3.connect(DB_PATH) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM relationships WHERE table_a='character' AND id_a=1 AND table_b='location' AND id_b=1"
        ).fetchone()[0]
        assert count == 1
        conn.commit()

    remove_entry = {
        'table_name': 'character',
        'record_id': 1,
        'field_name': 'relation_location',
        'old_value': '1',
        'new_value': None,
    }
    assert revert_edit(remove_entry)

    with sqlite3.connect(DB_PATH) as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM relationships WHERE table_a='character' AND id_a=1 AND table_b='location' AND id_b=1"
        ).fetchone()[0]
        assert count == 0
        log_count = conn.execute(
            'SELECT COUNT(*) FROM edit_history WHERE id > ?',
            (max_id,)
        ).fetchone()[0]
        assert log_count == 4
        conn.execute(
            'DELETE FROM relationships WHERE table_a="character" AND id_a=1 AND table_b="location" AND id_b=1'
        )
        conn.execute('DELETE FROM edit_history WHERE id > ?', (max_id,))
        conn.commit()


def test_revert_edit_invalid_table():
    entry = {
        'table_name': 'invalid',
        'record_id': 1,
        'field_name': 'character',
        'old_value': 'a',
        'new_value': 'b',
    }
    assert revert_edit(entry) is False
