import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
from imports import tasks as import_tasks

app.testing = True
client = app.test_client()


def test_import_start_and_status():
    import_tasks.huey.immediate = True
    payload = {
        'table': 'character',
        'rows': [
            {'character': 'Test Character'}
        ]
    }
    resp = client.post('/import-start', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'importId' in data
    import_id = data['importId']

    status_resp = client.get('/import-status', query_string={'importId': import_id})
    assert status_resp.status_code == 200
    status = status_resp.get_json()
    assert status['status'] == 'complete'
    assert status['importedRows'] == len(payload['rows'])
