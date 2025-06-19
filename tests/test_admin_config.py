import re


def test_log_level_field_is_select(client):
    resp = client.get('/admin/config')
    assert resp.status_code == 200
    html = resp.data.decode()
    m = re.search(r'log_level</td>\s*<td[^>]*>\s*<form[^>]*>(.*?)</form>', html, re.S)
    assert m is not None
    row_html = m.group(1)
    assert '<select' in row_html
    options = re.findall(r'<option value="([^"]+)"', row_html)
    assert {'DEBUG', 'INFO', 'WARNING', 'ERROR'}.issubset(set(options))


def test_config_db_upload_redirects(client, monkeypatch):
    import io
    from views.admin import config as cfg

    monkeypatch.setattr(cfg, 'initialize_database', lambda *a, **k: None)
    monkeypatch.setattr(cfg, 'ensure_default_configs', lambda *a, **k: None)
    monkeypatch.setattr(cfg, 'init_db_path', lambda *a, **k: None)
    monkeypatch.setattr(cfg, 'update_config', lambda *a, **k: None)
    monkeypatch.setattr(cfg, 'reload_app_state', lambda: None)

    data = {'file': (io.BytesIO(b'data'), 'temp.db')}
    resp = client.post('/admin/config/db', data=data, content_type='multipart/form-data')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/admin/database')


def test_config_db_create_redirects_to_wizard(client, monkeypatch):
    from views.admin import config as cfg

    monkeypatch.setattr(cfg, 'initialize_database', lambda *a, **k: None)
    monkeypatch.setattr(cfg, 'ensure_default_configs', lambda *a, **k: None)
    monkeypatch.setattr(cfg, 'init_db_path', lambda *a, **k: None)
    monkeypatch.setattr(cfg, 'update_config', lambda *a, **k: None)
    monkeypatch.setattr(cfg, 'reload_app_state', lambda: None)

    resp = client.post('/admin/config/db', data={'create_name': 'new.db'})
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/wizard/')
    with client.session_transaction() as sess:
        assert sess['wizard_progress'] == {'database': True, 'skip_import': True}
        assert 'wizard_complete' not in sess


def test_db_create_updates_path_and_allows_table_creation(client):
    import os
    import sqlite3
    from main import app
    from views.admin import reload_app_state
    import db.database as db_database
    from db.config import update_config

    new_name = 'admin_created.db'
    new_path = os.path.join('data', new_name)
    try:
        os.remove(new_path)
    except FileNotFoundError:
        pass

    resp = client.post('/admin/config/db', data={'create_name': new_name})
    assert resp.status_code == 302
    assert os.path.abspath(new_path) == db_database.DB_PATH

    table = 'admintest'
    resp = client.post('/add-table', json={'table_name': table, 'description': 'x'})
    assert resp.status_code == 200
    assert resp.get_json()['success']

    with sqlite3.connect(db_database.DB_PATH) as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        assert row is not None

    with sqlite3.connect('data/crossbook.db') as conn:
        row = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,),
        ).fetchone()
        assert row is None

    update_config('db_path', 'data/crossbook.db')
    with app.app_context():
        reload_app_state()
