import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app

app.testing = True
client = app.test_client()


def test_wizard_start_without_progress_redirects_home():
    resp = client.get('/wizard/')
    assert resp.status_code == 302
    assert resp.headers['Location'].endswith('/')
