import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import init_db_path
from db.query_filters import _build_filters
from db.schema import get_field_schema

init_db_path('data/crossbook.db')


def test_build_filters_search_clause():
    fields = [
        f
        for f, meta in get_field_schema()['character'].items()
        if meta['type'] in ('text', 'textarea', 'select', 'multi_select', 'url')
    ]
    clauses, params = _build_filters('character', search='foo')
    assert len(clauses) == 1
    clause = clauses[0]
    assert clause.startswith('(') and clause.endswith(')')
    parts = clause[1:-1].split(' OR ')
    assert set(parts) == {f"{f} LIKE ?" for f in fields}
    assert params == ['%foo%'] * len(fields)


def test_build_filters_multiple_values_any_mode():
    clauses, params = _build_filters('content', filters={'tags': ['magic', 'quest']})
    assert clauses == ['(tags LIKE ? OR tags LIKE ?)']
    assert params == ['%magic%', '%quest%']


def test_build_filters_multiple_values_all_equals():
    clauses, params = _build_filters(
        'content',
        filters={'linenumber': [1, 2]},
        ops={'linenumber': 'equals'},
        modes={'linenumber': 'all'},
    )
    assert clauses == ['(linenumber = ? AND linenumber = ?)']
    assert params == [1, 2]


def test_build_filters_regex_operator():
    clauses, params = _build_filters(
        'content',
        filters={'chapter': '^Intro'},
        ops={'chapter': 'regex'},
    )
    assert clauses == ['(chapter REGEXP ?)']
    assert params == ['^Intro']


def test_apply_date_ranges():
    clauses, params = _build_filters(
        'content',
        filters={'date_created_start': '2023-01-01', 'date_created_end': '2023-01-31'},
    )
    assert clauses == ['date_created BETWEEN ? AND ?']
    assert params == ['2023-01-01', '2023-01-31']

    clauses, params = _build_filters(
        'content',
        filters={'date_created_start': '2023-01-01'},
    )
    assert clauses == ['date_created >= ?']
    assert params == ['2023-01-01']

    clauses, params = _build_filters(
        'content',
        filters={'date_created_end': '2023-01-31'},
    )
    assert clauses == ['date_created <= ?']
    assert params == ['2023-01-31']

