import sqlite3
import json
from db.database import get_connection
from db.config import get_layout_defaults

DEFAULT_FIELD_WIDTH = {
    "textarea":   12,
    "select":      5,
    "text":       12,
    "foreign_key": 5,
    "boolean":     3,
    "number":      4,
    "multi_select": 6
}

DEFAULT_FIELD_HEIGHT = {
    "textarea":   18,
    "select":      4,
    "text":         4,
    "foreign_key": 10,
    "boolean":      7,
    "number":       3,
    "multi_select":  8
}


def add_field_to_schema(table, field_name, field_type, field_options=None, foreign_key=None, layout=None):
    """Insert a new field into the field_schema table."""
    with get_connection() as conn:
        cur = conn.cursor()

        # 1) Serialize the list of options (if any) to JSON text
        options_str = json.dumps(field_options or [])

        # 2) Compute the new field's row_start by finding the current bottom edge
        cur.execute(
            "SELECT COALESCE(MAX(row_start + row_span), 0) FROM field_schema WHERE table_name = ?",
            (table,),
        )
        max_bottom = cur.fetchone()[0]  # if no rows yet, that's 0

        # 3) Determine col_start, col_span, row_start, row_span
        defaults = get_layout_defaults() or {}
        width_map = defaults.get('width', DEFAULT_FIELD_WIDTH)
        height_map = defaults.get('height', DEFAULT_FIELD_HEIGHT)

        col_start = 0
        col_span = width_map.get(field_type, 6)
        row_start = max_bottom
        row_span = height_map.get(field_type, 4)

        # 4) Insert into field_schema with the nine real columns
        cur.execute(
            """
            INSERT INTO field_schema
              (table_name, field_name, field_type, field_options, foreign_key,
               col_start, col_span, row_start, row_span)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                table,
                field_name,
                field_type,
                options_str,
                foreign_key,
                col_start,
                col_span,
                row_start,
                row_span,
            ),
        )
        conn.commit()

def add_column_to_table(table_name, field_name, field_type):
    from db.database import get_connection

    # Map form types to SQL types
    SQL_TYPE_MAP = {
        "text": "TEXT",
        "number": "REAL",
        "date": "TEXT",
        "boolean": "INTEGER",
        "textarea": "TEXT",
        "select": "TEXT",
        "multi_select": "TEXT",
        "foreign_key": "TEXT"
    }

    sql_type = SQL_TYPE_MAP.get(field_type)
    if not sql_type:
        raise ValueError(f"Unsupported field type: {field_type}")

    # Validate names are safe (simple alphanumeric check)
    if not table_name.isidentifier():
        raise ValueError(f"Invalid table name: {table_name}")
    if not field_name.isidentifier():
        raise ValueError(f"Invalid field name: {field_name}")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{field_name}" {sql_type}')
        conn.commit()

def drop_column_from_table(table, field_name):
    with get_connection() as conn:
        cur = conn.cursor()

        # 1) Get column names, excluding the one to remove
        cur.execute(f"PRAGMA table_info('{table}')")
        all_cols = [row[1] for row in cur.fetchall()]
        remaining = [c for c in all_cols if c != field_name]
        if len(remaining) == len(all_cols):
            return

        cols_csv = ", ".join(f'"{c}"' for c in remaining)
        temp_table = f"{table}_temp"

        # 2) Create temp table copying data
        cur.execute(f'CREATE TABLE "{temp_table}" AS SELECT {cols_csv} FROM "{table}"')
        # 3) Drop original
        cur.execute(f'DROP TABLE "{table}"')
        # 4) Rename temp to original
        cur.execute(f'ALTER TABLE "{temp_table}" RENAME TO "{table}"')

        conn.commit()

def remove_field_from_schema(table, field_name):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "DELETE FROM field_schema WHERE table_name = ? AND field_name = ?",
            (table, field_name),
        )
        conn.commit()
