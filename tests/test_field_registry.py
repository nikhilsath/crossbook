import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.field_registry import register_type, get_field_type, get_type_size_map, FIELD_TYPES


def test_register_get_and_size_map():
    # ensure clean state
    if 'tmp_test' in FIELD_TYPES:
        FIELD_TYPES.pop('tmp_test')
    register_type(
        'tmp_test',
        sql_type='INTEGER',
        default_width=7,
        default_height=9,
        macro='render_text',
        searchable=True,
        allows_multiple=True,
        is_textarea=True,
        is_boolean=True,
        is_url=True,
    )

    ft = get_field_type('tmp_test')
    assert ft.name == 'tmp_test'
    assert ft.sql_type == 'INTEGER'

    assert ft.searchable is True

    size_map = get_type_size_map()
    assert size_map['tmp_test'] == (7, 9)
    assert ft.macro == 'render_text'
    assert ft.allows_multiple is True
    assert ft.is_textarea is True
    assert ft.is_boolean is True
    assert ft.is_url is True

    FIELD_TYPES.pop('tmp_test', None)
