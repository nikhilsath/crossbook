import os
import sys
import sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
from db.database import init_db_path

init_db_path('data/crossbook.db')
app.testing = True
client = app.test_client()

DB_PATH = 'data/crossbook.db'

def test_textarea_update_sanitizes_html():
    with sqlite3.connect(DB_PATH) as conn:
        record_id = conn.execute('SELECT id FROM character LIMIT 1').fetchone()[0]

    payload = "<script>alert(1)</script><p>Hello</p>"
    resp = client.post(f'/character/{record_id}/update', data={'field': 'description', 'new_value': payload})
    assert resp.status_code in (200, 302)

    with sqlite3.connect(DB_PATH) as conn:
        value = conn.execute('SELECT description FROM character WHERE id = ?', (record_id,)).fetchone()[0]

    assert '<script>' not in value
    assert '<p>Hello</p>' in value
