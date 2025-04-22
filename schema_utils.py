import sqlite3
import json

DB_PATH = "data/crossbook.db"

DEFAULT_LAYOUTS = {
    "textarea":     {"width": "100%", "minWidth": "300px"},
    "multi_select": {"width": "200px", "minWidth": "250px"},
    "boolean":      {"width": "auto", "minWidth": "100px"},
    "select":       {"width": "50%", "minWidth": "120px"},
    "text":         {"width": "50%", "minWidth": "200px"},
    "number":       {"width": "auto", "minWidth": "120px"},
    "date":         {"width": "auto", "minWidth": "150px"},
    "foreign_key":  {"width": "auto%", "minWidth": "250px"},
}

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

def backfill_layout_defaults():
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT table_name, field_name, field_type, layout FROM field_schema")
        updates = []

        for table_name, field_name, field_type, layout in cur.fetchall():
            if layout and layout.strip() not in ("", "{}"):
                continue  # already set

            base_type = field_type.strip().lower()
            layout_json = DEFAULT_LAYOUTS.get(base_type)
            if layout_json:
                updates.append((json.dumps(layout_json), table_name, field_name))

        for layout, table_name, field_name in updates:
            cur.execute(
                "UPDATE field_schema SET layout = ? WHERE table_name = ? AND field_name = ?",
                (layout, table_name, field_name)
            )

        conn.commit()
        print(f"Backfilled layout for {len(updates)} fields.")

def load_field_layout():
    import json
    import sqlite3
    from main import DB_PATH

    layout = {}
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT table_name, field_name, layout FROM field_schema")
    for table, field, layout_raw in cur.fetchall():
        layout.setdefault(table, {})
        try:
            layout[table][field] = json.loads(layout_raw or "{}")
        except Exception:
            layout[table][field] = {}
    return layout
