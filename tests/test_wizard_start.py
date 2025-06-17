


def test_wizard_start_without_progress_redirects_home(client):
    resp = client.get('/wizard/')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')
