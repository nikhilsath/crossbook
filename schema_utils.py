import sqlite3
import json

DB_PATH = "data/crossbook.db"

def load_field_schema():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT table_name, field_name, field_type FROM field_schema")
    rows = cur.fetchall()
    schema = {}
    for table, field, ftype in rows:
        schema.setdefault(table, {})[field] = ftype
    return schema

def get_field_options(table, field):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT field_options FROM field_schema WHERE table_name = ? AND field_name = ?", (table, field))
    row = cur.fetchone()
    if row and row[0]:
        try:
            return json.loads(row[0])
        except Exception:
            return []
    return []
