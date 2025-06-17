import pytest


def test_wizard_start_without_progress_redirects_home(client):
    resp = client.get('/wizard/')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')


def test_wizard_start_completes_session(client):
    with client.session_transaction() as sess:
        sess['wizard_progress'] = {
            'database': True,
            'settings': True,
            'table': True,
            'skip_import': True,
        }
    resp = client.get('/wizard/')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')
    with client.session_transaction() as sess:
        assert sess.get('wizard_complete') is True
        assert 'wizard_progress' not in sess


def test_skip_import_sets_flag(client):
    with client.session_transaction() as sess:
        sess['wizard_progress'] = {'database': True}
    resp = client.get('/wizard/skip-import')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/wizard/')
    with client.session_transaction() as sess:
        assert sess['wizard_progress']['skip_import'] is True


def test_skip_import_completion(client):
    with client.session_transaction() as sess:
        sess['wizard_progress'] = {
            'database': True,
            'settings': True,
            'table': True,
        }
    resp = client.get('/wizard/skip-import', follow_redirects=True)
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get('wizard_complete') is True
        assert 'wizard_progress' not in sess
