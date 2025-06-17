


def test_skip_import_route(client):
    with client.session_transaction() as sess:
        sess['wizard_progress'] = {'database': True, 'settings': True, 'table': True}
    resp = client.get('/wizard/skip-import', follow_redirects=True)
    assert resp.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get('wizard_complete') is True
        assert 'wizard_progress' not in sess
