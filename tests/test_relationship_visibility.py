import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
from db.database import init_db_path
from db.config import get_relationship_visibility

init_db_path('data/crossbook.db')
app.testing = True
client = app.test_client()

DB_PATH = 'data/crossbook.db'

def test_update_relationship_visibility():
    resp = client.post('/character/relationships', json={'visibility': {'location': {'hidden': True, 'force': True}}})
    assert resp.status_code == 200
    assert resp.get_json()['success']
    vis = get_relationship_visibility()
    assert vis['character']['location']['hidden'] is True
    assert vis['character']['location']['force'] is True
