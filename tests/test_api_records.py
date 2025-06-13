import os
import sys
import sqlite3
from urllib.parse import parse_qs

# Ensure the app module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

app.testing = True
client = app.test_client()

DB_PATH = 'data/crossbook.db'

def expected_count(tags, mode='any'):
    with sqlite3.connect(DB_PATH) as conn:
        if mode == 'all':
            clause = ' AND '.join(['tags LIKE ?'] * len(tags))
        else:
            clause = ' OR '.join(['tags LIKE ?'] * len(tags))
        params = [f'%{t}%' for t in tags]
        cur = conn.execute(f'SELECT COUNT(*) FROM content WHERE {clause}', params)
        return cur.fetchone()[0]

def test_multi_select_any_mode():
    tags = ['Durza', 'Shade']
    resp = client.get('/api/content/records', query_string=[('tags', t) for t in tags])
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(parse_qs(data['base_qs'])['tags']) == set(tags)
    assert data['total_count'] == expected_count(tags, 'any')
    assert len(data['records']) == data['total_count']

def test_multi_select_all_mode():
    tags = ['Durza', 'Shade']
    resp = client.get('/api/content/records', query_string=[('tags', t) for t in tags] + [('tags_mode', 'all')])
    assert resp.status_code == 200
    data = resp.get_json()
    assert set(parse_qs(data['base_qs'])['tags']) == set(tags)
    assert data['total_count'] == expected_count(tags, 'all')
    assert len(data['records']) == data['total_count']


def test_bulk_update_route():
    ids = []
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute('SELECT id, character FROM character LIMIT 2')
        rows = cur.fetchall()
        ids = [r[0] for r in rows]
        originals = [r[1] for r in rows]

    resp = client.post('/character/bulk-update', json={'ids': ids, 'field': 'character', 'value': 'TestName'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] and data['updated'] == len(ids)

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute('SELECT character FROM character WHERE id IN (?, ?)', ids)
        values = [r[0] for r in cur.fetchall()]
    assert set(values) == {'TestName'}

    # revert changes
    with sqlite3.connect(DB_PATH) as conn:
        for i, val in zip(ids, originals):
            conn.execute('UPDATE character SET character = ? WHERE id = ?', (val, i))
        conn.commit()


def test_bulk_update_multiselect():
    ids = []
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute('SELECT id, tags FROM content LIMIT 2')
        rows = cur.fetchall()
        ids = [r[0] for r in rows]
        originals = [r[1] for r in rows]

    new_tags = ['magic', 'quest']
    resp = client.post('/content/bulk-update', json={'ids': ids, 'field': 'tags', 'value': new_tags})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] and data['updated'] == len(ids)

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute('SELECT tags FROM content WHERE id IN (?, ?)', ids)
        values = [r[0] for r in cur.fetchall()]
    assert set(values) == {', '.join(new_tags)}

    with sqlite3.connect(DB_PATH) as conn:
        for i, val in zip(ids, originals):
            conn.execute('UPDATE content SET tags = ? WHERE id = ?', (val, i))
        conn.commit()


def test_url_field_add_update_and_bulk():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute('SELECT id FROM character LIMIT 2')
        rows = cur.fetchall()
        record_ids = [r[0] for r in rows]
    record_id = record_ids[0]

    resp = client.post(f'/character/{record_id}/add-field', data={'field_name': 'website', 'field_type': 'url'})
    assert resp.status_code in (302, 200)

    with sqlite3.connect(DB_PATH) as conn:
        cols = [r[1] for r in conn.execute('PRAGMA table_info(character)').fetchall()]
        assert 'website' in cols

    resp = client.post(f'/character/{record_id}/update', data={'field': 'website', 'new_value': 'https://example.com'})
    assert resp.status_code in (302, 200)

    resp = client.get('/api/character/records', query_string={'website': 'https://example.com', 'website_op': 'equals', 'id': record_id, 'id_op': 'equals'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert any(r['id'] == record_id and r.get('website') == 'https://example.com' for r in data['records'])

    resp = client.post('/character/bulk-update', json={'ids': record_ids, 'field': 'website', 'value': 'https://bulk.com'})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['success'] and data['updated'] == len(record_ids)

    with sqlite3.connect(DB_PATH) as conn:
        vals = [r[0] for r in conn.execute('SELECT website FROM character WHERE id IN (?, ?)', record_ids).fetchall()]
    assert set(vals) == {'https://bulk.com'}

    from db.edit_fields import drop_column_from_table, remove_field_from_schema
    drop_column_from_table('character', 'website')
    remove_field_from_schema('character', 'website')

