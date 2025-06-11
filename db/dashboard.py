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
    conn = get_connection()
    cursor = conn.cursor()
    try:
        sql = f'SELECT SUM("{field}") FROM "{table}"'
        cursor.execute(sql)
        result = cursor.fetchone()[0]
        return result or 0
    except Exception as e:
        logger.warning(f"[sum_field] SQL error for {table}.{field}: {e}")
        return 0
    finally:
        conn.close()


def get_dashboard_widgets() -> list[dict]:
    """Return all dashboard widgets ordered by id."""
    conn = get_connection()
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
    finally:
        conn.close()
