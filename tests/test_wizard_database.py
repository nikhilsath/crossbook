import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
import db.database as db_database
from db.config import get_config_rows

app.testing = True
client = app.test_client()


def test_settings_step_after_db_creation():
    new_name = 'test_created.db'
    # ensure file removed if exists from prior runs
    try:
        os.remove(os.path.join('data', new_name))
    except FileNotFoundError:
        pass

    resp = client.post('/wizard/database', data={'create_name': new_name}, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Step 2' in resp.data
    assert os.path.abspath(os.path.join('data', new_name)) == db_database.DB_PATH

    rows = get_config_rows()
    config = {row['key']: row['value'] for row in rows}
    assert config.get('db_path')
    assert config.get('heading') == ''
    # ensure other defaults exist and metadata copied
    assert 'log_level' in config
    meta = {row['key']: row for row in rows}
    assert meta['log_level']['section'] == 'logging'
    assert meta['log_level']['type'] == 'select'
    assert meta['log_level']['options']

    # restore original test database
    from db.database import init_db_path
    from db.config import update_config
    init_db_path('data/crossbook.db')
    update_config('db_path', 'data/crossbook.db')
    from views.admin import reload_app_state
    with app.app_context():
        reload_app_state()
