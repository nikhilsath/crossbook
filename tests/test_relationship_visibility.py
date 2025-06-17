import json
from db.config import get_relationship_visibility

def test_update_relationship_visibility(client):
    resp = client.post('/character/relationships', json={'visibility': {'location': {'hidden': True, 'force': True}}})
    assert resp.status_code == 200
    assert resp.get_json()['success']
    vis = get_relationship_visibility()
    assert vis['character']['location']['hidden'] is True
    assert vis['character']['location']['force'] is True
