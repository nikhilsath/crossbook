import os
import sys
import json
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from db.database import init_db_path
from db.config import update_config, get_config_rows

init_db_path('data/crossbook.db')
app.testing = True
client = app.test_client()


def test_crawler_scan_counts_enabled_folders(tmp_path):
    enabled_dir = tmp_path / 'enabled'
    disabled_dir = tmp_path / 'disabled'
    enabled_dir.mkdir()
    disabled_dir.mkdir()
    for i in range(3):
        (enabled_dir / f'e{i}.txt').write_text('x')
    for i in range(2):
        (disabled_dir / f'd{i}.txt').write_text('x')

    folders = [
        {'path': str(enabled_dir), 'enabled': True},
        {'path': str(disabled_dir), 'enabled': False},
    ]
    update_config('crawler_folders', json.dumps(folders))

    resp = client.post('/crawler/scan')
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['file_count'] == 3

    rows = get_config_rows()
    cfg = {r['key']: r['value'] for r in rows}
    assert int(cfg.get('crawler_file_count')) == 3

    resp = client.get('/crawler')
    assert resp.status_code == 200
    assert resp.get_json()['file_count'] == 3
