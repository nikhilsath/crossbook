import sqlite3
from db.database import DB_PATH
from db.config import get_layout_defaults, update_config
from utils.field_registry import get_type_size_map


def test_get_layout_defaults_uses_registry():
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT value FROM config WHERE key='layout_defaults'").fetchone()
        original = row[0] if row else ''
    try:
        update_config('layout_defaults', '')
        defaults = get_layout_defaults()
        size_map = get_type_size_map()
        expected = {
            'width': {k: v[0] for k, v in size_map.items()},
            'height': {k: v[1] for k, v in size_map.items()},
        }
        assert defaults == expected
    finally:
        update_config('layout_defaults', original)
