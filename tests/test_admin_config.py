import os
import sys
import re
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from main import app
from db.database import init_db_path

init_db_path('data/crossbook.db')

app.testing = True
client = app.test_client()

def test_log_level_field_is_select():
    resp = client.get('/admin/config')
    assert resp.status_code == 200
    html = resp.data.decode()
    m = re.search(r'log_level</td>\s*<td[^>]*>\s*<form[^>]*>(.*?)</form>', html, re.S)
    assert m is not None
    row_html = m.group(1)
    assert '<select' in row_html
    options = re.findall(r'<option value="([^"]+)"', row_html)
    assert {'DEBUG', 'INFO', 'WARNING', 'ERROR'}.issubset(set(options))
