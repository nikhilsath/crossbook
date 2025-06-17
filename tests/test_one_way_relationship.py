import os, sys, sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from db.database import init_db_path
from db.relationships import get_related_records

init_db_path('data/crossbook.db')
app.testing = True
client = app.test_client()

DB_PATH = 'data/crossbook.db'


def test_add_one_way_relationship():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM relationships WHERE table_a=? AND id_a=? AND table_b=? AND id_b=?",
            ('character', 1, 'location', 1),
        )
        conn.commit()

    resp = client.post(
        '/relationship',
        json={
            'table_a': 'character',
            'id_a': 1,
            'table_b': 'location',
            'id_b': 1,
            'action': 'add',
            'two_way': False,
        },
    )
    assert resp.status_code == 200
    assert resp.get_json()['success']

    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute(
            "SELECT two_way FROM relationships WHERE table_a=? AND id_a=? AND table_b=? AND id_b=?",
            ('character', 1, 'location', 1),
        ).fetchone()
        assert row is not None and row[0] == 0

    related = get_related_records('character', 1)
    assert 'location' in related
    item = next(i for i in related['location']['items'] if i['id'] == 1)
    assert item['two_way'] is False

    resp = client.post(
        '/relationship',
        json={
            'table_a': 'character',
            'id_a': 1,
            'table_b': 'location',
            'id_b': 1,
            'action': 'remove',
        },
    )
    assert resp.status_code == 200
    assert resp.get_json()['success']
