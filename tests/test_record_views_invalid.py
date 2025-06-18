import sqlite3
from db.database import init_db_path

DB_PATH = 'data/crossbook.db'

# ensure DB path is set for standalone running
init_db_path(DB_PATH)


def test_update_field_missing_field(client):
    before = sqlite3.connect(DB_PATH).execute(
        "SELECT character FROM character WHERE id=1"
    ).fetchone()[0]
    resp = client.post('/character/1/update', data={'new_value': 'X'})
    assert resp.status_code == 400
    after = sqlite3.connect(DB_PATH).execute(
        "SELECT character FROM character WHERE id=1"
    ).fetchone()[0]
    assert after == before


def test_bulk_update_bad_json(client):
    with sqlite3.connect(DB_PATH) as conn:
        ids = [r[0] for r in conn.execute('SELECT id FROM character LIMIT 2')]
        before = [r[0] for r in conn.execute(
            'SELECT character FROM character WHERE id IN (?, ?)', ids
        )]

    resp = client.post('/character/bulk-update', json={'ids': ids})
    assert resp.status_code == 400

    with sqlite3.connect(DB_PATH) as conn:
        after = [r[0] for r in conn.execute(
            'SELECT character FROM character WHERE id IN (?, ?)', ids
        )]
    assert after == before


def test_update_layout_bad_json(client):
    before = sqlite3.connect(DB_PATH).execute(
        "SELECT col_start, col_span, row_start, row_span FROM field_schema WHERE table_name='character' AND field_name='character'"
    ).fetchone()
    resp = client.post('/character/layout', json={'layout': 'bad'})
    assert resp.status_code == 400
    after = sqlite3.connect(DB_PATH).execute(
        "SELECT col_start, col_span, row_start, row_span FROM field_schema WHERE table_name='character' AND field_name='character'"
    ).fetchone()
    assert after == before


def test_manage_relationship_invalid_action(client):
    before_count = sqlite3.connect(DB_PATH).execute(
        'SELECT COUNT(*) FROM relationships'
    ).fetchone()[0]
    resp = client.post('/relationship', json={
        'action': 'unknown',
        'table_a': 'character',
        'id_a': 1,
        'table_b': 'location',
        'id_b': 1
    })
    assert resp.status_code == 400
    after_count = sqlite3.connect(DB_PATH).execute(
        'SELECT COUNT(*) FROM relationships'
    ).fetchone()[0]
    assert after_count == before_count
