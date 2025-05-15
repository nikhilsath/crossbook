import sqlite3
import json
from db.database import get_connection

def add_field():
    add_field_to_schema()
    add_column_to_table()

def add_field_to_schema(table, field_name, field_type, field_options=None, foreign_key=None, layout=None):
    conn = get_connection()
    cur = conn.cursor()
    
    options_str = json.dumps(field_options or [])
    layout_str = json.dumps(layout or {})

    cur.execute("""
        INSERT INTO field_schema (table_name, field_name, field_type, field_options, foreign_key, layout)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (table, field_name, field_type, options_str, foreign_key, layout_str))
    
    conn.commit()

def add_column_to_table(table_name, field_name, field_type):
    import sqlite3
    from db.database import get_connection

    # Map form types to SQL types
    SQL_TYPE_MAP = {
        "text": "TEXT",
        "number": "REAL",
        "date": "TEXT",
        "boolean": "INTEGER",
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
