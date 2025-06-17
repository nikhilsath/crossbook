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


def test_boolean_and_date_inputs_render_correctly():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value, section, type, wizard) VALUES ('bool_setting', '1', 'general', 'boolean', 1)"
        )
        conn.execute(
            "INSERT OR REPLACE INTO config (key, value, section, type, wizard) VALUES ('date_setting', '2025-01-01', 'general', 'date', 1)"
        )
        conn.commit()
    try:
        with client.session_transaction() as sess:
            sess['wizard_progress'] = {'database': True}
        resp = client.get('/wizard/settings')
        assert resp.status_code == 200
        html = resp.data.decode()
        assert '<input type="checkbox" name="bool_setting"' in html
        assert '<input type="date" name="date_setting"' in html
    finally:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM config WHERE key IN ('bool_setting', 'date_setting')")
            conn.commit()
