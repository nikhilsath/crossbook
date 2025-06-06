import sqlite3
import json
from db.database import get_connection

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
    """
    Insert a new field into the field_schema table, placing it at the bottom of the existing grid.

    We compute:
      - col_start = 0
      - col_span  = DEFAULT_FIELD_WIDTH[field_type]
      - row_start = (max over all existing row_start + row_span for this table)
      - row_span  = DEFAULT_FIELD_HEIGHT[field_type]
    """
    conn = get_connection()
    cur = conn.cursor()

    # 1) Serialize the list of options (if any) to JSON text
    options_str = json.dumps(field_options or [])

    # 2) Compute the new field's row_start by finding the current bottom edge
    cur.execute(
        "SELECT COALESCE(MAX(row_start + row_span), 0) FROM field_schema WHERE table_name = ?",
        (table,)
    )
    max_bottom = cur.fetchone()[0]  # if no rows yet, that's 0

    # 3) Determine col_start, col_span, row_start, row_span from defaults
    col_start = 0
    col_span  = DEFAULT_FIELD_WIDTH.get(field_type, 6)    # fall back to 6 if somehow missing
    row_start = max_bottom
    row_span  = DEFAULT_FIELD_HEIGHT.get(field_type, 4)   # fall back to 4 if missing

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
        )
    )
    conn.commit()
    conn.close()

def add_column_to_table(table_name, field_name, field_type):
    import sqlite3
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
    if not field_name.isidentifier():
        raise ValueError(f"Invalid field name: {field_name}")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f'ALTER TABLE "{table_name}" ADD COLUMN "{field_name}" {sql_type}')
    conn.commit()
    conn.close()

def drop_column_from_table(table, field_name):
 
    conn = get_connection()
    cur = conn.cursor()

    # 1) Get column names, excluding the one to remove
    cur.execute(f"PRAGMA table_info('{table}')")
    all_cols = [row[1] for row in cur.fetchall()]
    remaining = [c for c in all_cols if c != field_name]
    if len(remaining) == len(all_cols):
        # field_name not found; nothing to do
        conn.close()
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
    conn.close()

def remove_field_from_schema(table, field_name):
    conn = get_connection()
    cur = conn.cursor()

    # 1) Delete from the field_schema table in SQLite
    cur.execute(
        "DELETE FROM field_schema WHERE table_name = ? AND field_name = ?",
        (table, field_name)
    )
    conn.commit()
    conn.close()
