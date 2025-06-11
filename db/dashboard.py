import logging

from db.database import get_connection
from db.schema import get_field_schema
from db.validation import validate_table

logger = logging.getLogger(__name__)


def sum_field(table: str, field: str) -> float:
    """Return the sum of all values for a numeric field."""
    validate_table(table)
    fmeta = get_field_schema().get(table, {}).get(field)
    if fmeta is None or fmeta.get("type") != "number":
        raise ValueError(f"Invalid numeric field: {field}")
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            sql = f'SELECT SUM("{field}") FROM "{table}"'
            cursor.execute(sql)
            result = cursor.fetchone()[0]
            return result or 0
        except Exception as e:
            logger.warning(f"[sum_field] SQL error for {table}.{field}: {e}")
            return 0


def get_dashboard_widgets() -> list[dict]:
    """Return all dashboard widgets ordered by id."""
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, title, content, widget_type, col_start, col_span, row_start, row_span"
                " FROM dashboard_widget ORDER BY id"
            )
            rows = cursor.fetchall()
            cols = [d[0] for d in cursor.description]
            return [dict(zip(cols, r)) for r in rows]
        except Exception as e:
            logger.warning("[get_dashboard_widgets] SQL error: %s", e)
            return []


def create_widget(
    title: str,
    content: str,
    widget_type: str,
    col_start: int,
    col_span: int,
    row_start: int,
    row_span: int,
) -> int | None:
    """Insert a new widget row and return its id."""
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO dashboard_widget
                    (title, content, widget_type, col_start, col_span, row_start, row_span)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (title, content, widget_type, col_start, col_span, row_start, row_span),
            )
            conn.commit()
            return cur.lastrowid
        except Exception as exc:
            logger.warning("[create_widget] SQL error: %s", exc)
            return None
