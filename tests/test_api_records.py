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

