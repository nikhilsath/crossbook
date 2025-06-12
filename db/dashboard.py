import logging

from flask import current_app
from db.database import get_connection
from db.schema import get_field_schema
from db.validation import validate_table
from db.records import count_records, get_all_records

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


def get_next_row_start() -> int:
    """Return the next available row_start value for a new widget."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT COALESCE(MAX(row_start + row_span), 0) FROM dashboard_widget"
        )
        result = cur.fetchone()
        return int(result[0]) if result else 0


def create_widget(
    title: str,
    content: str,
    widget_type: str,
    col_start: int,
    col_span: int,
    row_start: int | None,
    row_span: int,
) -> int | None:
    """Insert a new widget row and return its id."""
    if row_start is None:
        row_start = get_next_row_start()

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


def update_widget_layout(layout_items: list[dict]) -> int:
    """Update the grid layout data for dashboard widgets.

    Args:
        layout_items: A list of dicts each containing ``id``, ``colStart``,
            ``colSpan``, ``rowStart`` and ``rowSpan``.

    Returns:
        The number of widget rows updated.
    """
    with get_connection() as conn:
        cur = conn.cursor()
        updated = 0

        for item in layout_items:
            widget_id = item.get("id")
            if widget_id is None:
                continue

            try:
                col_start = float(item.get("colStart", 0))
                col_span = float(item.get("colSpan", 0))
                row_start = float(item.get("rowStart", 0))
                row_span = float(item.get("rowSpan", 0))
            except (TypeError, ValueError):
                continue

            cur.execute(
                """
                UPDATE dashboard_widget
                   SET col_start = ?,
                       col_span  = ?,
                       row_start = ?,
                       row_span  = ?
                 WHERE id = ?
                """,
                (col_start, col_span, row_start, row_span, widget_id),
            )
            if cur.rowcount:
                updated += 1

        conn.commit()

    return updated


def get_base_table_counts() -> list[dict]:
    """Return record counts for each base table."""
    base_tables = current_app.config.get("BASE_TABLES", [])
    results: list[dict] = []
    for table in base_tables:
        try:
            cnt = count_records(table)
        except Exception as exc:
            logger.warning("[get_base_table_counts] error for %s: %s", table, exc)
            cnt = 0
        results.append({"table": table, "count": cnt})
    return results


def get_top_numeric_values(
    table: str,
    field: str,
    limit: int = 10,
    ascending: bool = False,
) -> list[dict]:
    """Return records ordered by a numeric field.

    Args:
        table: Table name.
        field: Numeric field to sort by.
        limit: Number of records to return.
        ascending: If True, return lowest values instead of highest.

    Returns:
        A list of ``{"id": id, "value": value}`` dictionaries.
    """
    validate_table(table)
    fmeta = get_field_schema().get(table, {}).get(field)
    if fmeta is None or fmeta.get("type") != "number":
        raise ValueError(f"Invalid numeric field: {field}")
    direction = "ASC" if ascending else "DESC"
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            sql = (
                f'SELECT id, "{field}" FROM "{table}" '
                f'WHERE "{field}" IS NOT NULL '
                f'ORDER BY "{field}" {direction} LIMIT ?'
            )
            cur.execute(sql, (int(limit),))
            rows = cur.fetchall()
            return [{"id": r[0], "value": r[1]} for r in rows]
        except Exception as exc:
            logger.warning(
                "[get_top_numeric_values] SQL error for %s.%s: %s", table, field, exc
            )
            return []


def get_filtered_records(
    table: str,
    filters: str | None = None,
    order_by: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """Return filtered records from a table.

    Args:
        table: Table name.
        filters: Optional search string applied across text fields.
        order_by: Field to order results by.
        limit: Maximum number of records to return.

    Returns:
        A list of record dictionaries.
    """
    validate_table(table)
    try:
        rows = get_all_records(
            table,
            search=filters,
            sort_field=order_by,
            limit=limit,
        )
        return rows
    except Exception as exc:
        logger.warning(
            "[get_filtered_records] error for %s: %s", table, exc
        )
        return []
