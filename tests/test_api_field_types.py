import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
from db.database import init_db_path

init_db_path('data/crossbook.db')
app.testing = True
client = app.test_client()

def test_api_field_types_returns_serializable_data():
    resp = client.get('/api/field-types')
    assert resp.status_code == 200
    data = resp.get_json()
    assert isinstance(data, dict)
    assert 'text' in data
    meta = data['text']
    assert isinstance(meta, dict)
    assert meta.get('sql_type') == 'TEXT'
    assert meta.get('allows_options') is False
