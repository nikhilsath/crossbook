import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
from db.database import init_db_path

init_db_path('data/crossbook.db')
app.testing = True
client = app.test_client()


def test_api_base_tables():
    resp = client.get('/api/base-tables')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, list)
    assert any(row['table_name'] == 'content' for row in data)

