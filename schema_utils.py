import sqlite3
import json

DB_PATH = "data/crossbook.db"

# Create library with field types 
def load_field_schema():
    import json
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT table_name, field_name, field_type, field_options, foreign_key, layout
        FROM field_schema
    """)
    rows = cur.fetchall()
    schema = {}

    for table, field, ftype, options, fk, layout_json in rows:
        schema.setdefault(table, {})[field] = {
            "type": ftype.strip(),
            "options": [],
            "foreign_key": fk,
            "layout": {}
        }

        # Parse options if present
        if options:
            try:
                schema[table][field]["options"] = json.loads(options)
            except Exception:
                schema[table][field]["options"] = []

        # Parse layout if present
        if layout_json:
            try:
                schema[table][field]["layout"] = json.loads(layout_json)
            except Exception:
                schema[table][field]["layout"] = {}

    return schema


def update_foreign_field_options():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Step 1: Fetch all foreign key fields
    cur.execute("""
        SELECT table_name, field_name, field_type, foreign_key
        FROM field_schema
        WHERE field_type = 'foreign_key'
    """)
    rows = cur.fetchall()

    for table_name, field_name, field_type, foreign_table in rows:
        if not foreign_table:
            continue  # Skip if foreign_table is null or empty

        # Step 2: Fetch id + display field from the foreign table
        try:
            cur.execute(f"PRAGMA table_info({foreign_table})")
            columns = [row[1] for row in cur.fetchall()]
            label_field = columns[1] if len(columns) > 1 else columns[0]

            cur.execute(f"SELECT id, {label_field} FROM {foreign_table}")
            options = [row[1] for row in cur.fetchall()]
        except Exception as e:
            print(f"Skipping {table_name}.{field_name} → {foreign_table}: {e}")
            continue

        # Step 3: Update the field_options column as JSON
        cur.execute("""
            UPDATE field_schema
            SET field_options = ?
            WHERE table_name = ? AND field_name = ?
        """, (json.dumps(options), table_name, field_name))

    conn.commit()
    conn.close()

