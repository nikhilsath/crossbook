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
