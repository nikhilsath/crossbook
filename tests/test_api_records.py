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

