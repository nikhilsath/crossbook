import os
import sys
import sqlite3
import json
import pytest

sys.path.insert(
    0, os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
)

from db.database import init_db_path
from db.dashboard import (
    sum_field,
    create_widget,
    update_widget_layout,
    update_widget_styling,
)

DB_PATH = "data/crossbook.db"
init_db_path(DB_PATH)


def fetch_value(sql, params=()):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.execute(sql, params)
        row = cur.fetchone()
        return row[0] if row else None


def test_sum_field_returns_correct_sum():
    expected = fetch_value("SELECT SUM(linenumber) FROM content")
    assert sum_field("content", "linenumber") == expected


def test_sum_field_raises_for_non_numeric():
    with pytest.raises(ValueError):
        sum_field("content", "content")  # 'content' field is not numeric


def test_create_widget_auto_row_start_and_id():
    start = fetch_value(
        "SELECT COALESCE(MAX(row_start + row_span), 0) FROM dashboard_widget"
    )
    widget_id = create_widget("Temp", "{}", "value", 1, 1, None, 1)
    assert isinstance(widget_id, int)
    row_start = fetch_value(
        "SELECT row_start FROM dashboard_widget WHERE id=?", (widget_id,)
    )
    assert row_start == start
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM dashboard_widget WHERE id=?", (widget_id,))
        conn.commit()


def test_update_widget_layout_multiple_and_ignore_invalid():
    id1 = create_widget("L1", "{}", "value", 1, 1, None, 1)
    id2 = create_widget("L2", "{}", "value", 1, 1, None, 1)
    layout = [
        {"id": id1, "colStart": 2, "colSpan": 2, "rowStart": 5, "rowSpan": 1},
        {"id": id2, "colStart": 3, "colSpan": 3, "rowStart": 6, "rowSpan": 2},
        {"colStart": 1},
        {
            "id": id2,
            "colStart": "x",
            "colSpan": 1,
            "rowStart": 1,
            "rowSpan": 1,
        },
        {
            "id": 999999,
            "colStart": 1,
            "colSpan": 1,
            "rowStart": 1,
            "rowSpan": 1,
        },
    ]
    updated = update_widget_layout(layout)
    assert updated == 2
    vals1 = fetch_value(
        "SELECT col_start FROM dashboard_widget WHERE id=?", (id1,)
    )
    vals2 = fetch_value(
        "SELECT row_span FROM dashboard_widget WHERE id=?", (id2,)
    )
    assert vals1 == 2
    assert vals2 == 2
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "DELETE FROM dashboard_widget WHERE id IN (?, ?)", (id1, id2)
        )
        conn.commit()


def test_update_widget_styling_valid_and_invalid():
    wid = create_widget("Style", "{}", "value", 1, 1, None, 1)
    assert update_widget_styling(wid, {"color": "red"}) is True
    stored = fetch_value(
        "SELECT styling FROM dashboard_widget WHERE id=?", (wid,)
    )
    assert json.loads(stored) == {"color": "red"}
    assert update_widget_styling(wid, {"bad": {1}}) is False
    stored_after = fetch_value(
        "SELECT styling FROM dashboard_widget WHERE id=?", (wid,)
    )
    assert stored_after == stored
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("DELETE FROM dashboard_widget WHERE id=?", (wid,))
        conn.commit()
