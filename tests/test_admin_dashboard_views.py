import json
import sqlite3

from main import app
from db.database import DB_PATH
from db.dashboard import (
    get_dashboard_widgets,
    update_widget_layout,
    update_widget_styling,
    get_top_numeric_values,
    get_filtered_records,
)
from db.records import count_records


def test_dashboard_page_displays_widgets(client):
    resp = client.get('/dashboard')
    assert resp.status_code == 200
    html = resp.data.decode()
    widgets = get_dashboard_widgets()
    assert widgets
    assert all(w['title'] in html for w in widgets)


def test_dashboard_create_widget_success(client):
    data = {
        'title': 'Temp Widget',
        'widget_type': 'value',
        'content': '42',
        'col_start': 1,
        'col_span': 1,
        'row_span': 1,
    }
    resp = client.post('/dashboard/widget', json=data)
    assert resp.status_code == 200
    j = resp.get_json()
    assert j['success']
    wid = j['id']
    widgets = get_dashboard_widgets()
    assert any(w['id'] == wid and w['title'] == 'Temp Widget' for w in widgets)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('DELETE FROM dashboard_widget WHERE id=?', (wid,))
        conn.commit()


def test_dashboard_create_widget_invalid_json(client):
    count_before = len(get_dashboard_widgets())
    data = {
        'title': 'Bad Chart',
        'widget_type': 'chart',
        'content': '{bad}',
    }
    resp = client.post('/dashboard/widget', json=data)
    assert resp.status_code == 400
    assert 'Invalid JSON' in resp.get_json().get('error', '')
    assert len(get_dashboard_widgets()) == count_before


def test_dashboard_create_widget_missing_fields(client):
    resp = client.post('/dashboard/widget', json={'title': ' ', 'widget_type': ''})
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'Missing required fields'


def test_dashboard_create_widget_invalid_type(client):
    data = {
        'title': 'Bad',
        'widget_type': 'unknown',
        'col_start': 1,
        'col_span': 1,
        'row_span': 1,
    }
    resp = client.post('/dashboard/widget', json=data)
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'Invalid widget type'


def test_dashboard_create_widget_invalid_layout(client):
    data = {
        'title': 'Bad',
        'widget_type': 'value',
        'col_start': 'x',
        'col_span': 1,
        'row_span': 1,
    }
    resp = client.post('/dashboard/widget', json=data)
    assert resp.status_code == 400
    assert resp.get_json()['error'] == 'Invalid layout values'


def test_dashboard_update_layout_success(client):
    widget = get_dashboard_widgets()[0]
    new_col = widget['col_start'] + 1
    payload = {
        'layout': [
            {
                'id': widget['id'],
                'colStart': new_col,
                'colSpan': widget['col_span'],
                'rowStart': widget['row_start'],
                'rowSpan': widget['row_span'],
            }
        ]
    }
    resp = client.post('/dashboard/layout', json=payload)
    assert resp.status_code == 200
    assert resp.get_json()['success']
    updated = next(w for w in get_dashboard_widgets() if w['id'] == widget['id'])
    assert updated['col_start'] == new_col
    update_widget_layout([
        {
            'id': widget['id'],
            'colStart': widget['col_start'],
            'colSpan': widget['col_span'],
            'rowStart': widget['row_start'],
            'rowSpan': widget['row_span'],
        }
    ])


def test_dashboard_update_layout_invalid_json(client):
    resp = client.post('/dashboard/layout', json={'bad': 1})
    assert resp.status_code == 400


def test_dashboard_update_style_success(client):
    widget = get_dashboard_widgets()[0]
    original = json.loads(widget.get('styling') or '{}')
    resp = client.post(
        '/dashboard/style',
        json={'widget_id': widget['id'], 'styling': {'color': 'blue'}},
    )
    assert resp.status_code == 200
    assert resp.get_json()['success']
    updated = next(w for w in get_dashboard_widgets() if w['id'] == widget['id'])
    assert json.loads(updated['styling']) == {'color': 'blue'}
    update_widget_styling(widget['id'], original)


def test_dashboard_update_style_invalid_data(client):
    resp = client.post('/dashboard/style', json={'widget_id': None, 'styling': 'x'})
    assert resp.status_code == 400


def test_dashboard_base_count(client):
    with app.app_context():
        app.config['BASE_TABLES'] = ['content', 'character']
    resp = client.get('/dashboard/base-count')
    assert resp.status_code == 200
    expected = [
        {'table': 'content', 'count': count_records('content')},
        {'table': 'character', 'count': count_records('character')},
    ]
    assert resp.get_json() == expected


def test_dashboard_top_numeric_success(client):
    resp = client.get(
        '/dashboard/top-numeric',
        query_string={'table': 'content', 'field': 'linenumber', 'limit': 3},
    )
    assert resp.status_code == 200
    assert resp.get_json() == get_top_numeric_values('content', 'linenumber', limit=3)


def test_dashboard_top_numeric_invalid_field(client):
    resp = client.get('/dashboard/top-numeric', query_string={'table': 'content', 'field': 'chapter'})
    assert resp.status_code == 400
    assert resp.get_json() == []


def test_dashboard_filtered_records_success(client):
    resp = client.get(
        '/dashboard/filtered-records',
        query_string={'table': 'content', 'search': 'Shade', 'order_by': 'id', 'limit': 5},
    )
    assert resp.status_code == 200
    assert resp.get_json() == get_filtered_records('content', filters='Shade', order_by='id', limit=5)


def test_dashboard_filtered_records_invalid_table(client):
    resp = client.get('/dashboard/filtered-records', query_string={'table': 'bad'})
    assert resp.status_code == 400
    assert resp.get_json() == []
