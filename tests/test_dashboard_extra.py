import os
import sys
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from db.database import init_db_path
from db.dashboard import (
    get_dashboard_widgets,
    get_base_table_counts,
    get_top_numeric_values,
    get_filtered_records,
)
from db.records import count_records

DB_PATH = 'data/crossbook.db'
init_db_path(DB_PATH)


def test_get_dashboard_widgets_list():
    widgets = get_dashboard_widgets()
    assert any(w["title"] == "Sum of linenumber" for w in widgets)
    assert set(widgets[0].keys()) >= {"id", "title", "content", "widget_type", "col_start"}


def test_get_base_table_counts_matches_record_counts():
    with app.app_context():
        app.config['BASE_TABLES'] = ['content', 'character']
        counts = get_base_table_counts()
    expected = [
        {'table': 'content', 'count': count_records('content')},
        {'table': 'character', 'count': count_records('character')},
    ]
    assert counts == expected


def test_get_top_numeric_values_ascending_and_descending():
    desc = get_top_numeric_values('content', 'linenumber', limit=3)
    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute('SELECT id, linenumber FROM content WHERE linenumber IS NOT NULL ORDER BY linenumber DESC LIMIT 3').fetchall()
    assert [(r['id'], r['value']) for r in desc] == [(row[0], row[1]) for row in rows]

    asc = get_top_numeric_values('content', 'linenumber', limit=3, ascending=True)
    with sqlite3.connect(DB_PATH) as conn:
        rows_asc = conn.execute('SELECT id, linenumber FROM content WHERE linenumber IS NOT NULL ORDER BY linenumber ASC LIMIT 3').fetchall()
    assert [(r['id'], r['value']) for r in asc] == [(row[0], row[1]) for row in rows_asc]


def test_get_filtered_records_with_search_limit():
    records = get_filtered_records('content', 'Shade', order_by='id', limit=5)
    assert len(records) == 5
    assert all('Shade' in r.get('chapter', '') for r in records)

