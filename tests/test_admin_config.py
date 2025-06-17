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
