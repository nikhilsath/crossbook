import sqlite3

def test_textarea_update_sanitizes_html(client, db_path):
    with sqlite3.connect(db_path) as conn:
        record_id = conn.execute('SELECT id FROM character LIMIT 1').fetchone()[0]

    payload = "<script>alert(1)</script><p>Hello</p>"
    resp = client.post(f'/character/{record_id}/update', data={'field': 'description', 'new_value': payload})
    assert resp.status_code in (200, 302)

    with sqlite3.connect(db_path) as conn:
        value = conn.execute('SELECT description FROM character WHERE id = ?', (record_id,)).fetchone()[0]

    assert '<script>' not in value
    assert '<p>Hello</p>' in value
