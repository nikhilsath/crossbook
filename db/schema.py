import sqlite3
import json

DB_PATH = "data/crossbook.db"
FIELD_SCHEMA = {}

DB_PATH = "data/crossbook.db"

# Create library with field types and coordinate layouts
def load_field_schema():
    """
    Load field definitions from the field_schema table into a nested dict
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Select all schema columns including new coordinates
    cur.execute("""
        SELECT table_name,
               field_name,
               field_type,
               field_options,
               foreign_key,
               left_pct,
               width_pct,
               top_em,
               height_em
        FROM field_schema
    """)
    rows = cur.fetchall()
    schema = {}

    for table, field, ftype, options, fk, left_pct, width_pct, top_em, height_em in rows:
        # Initialize field schema entry
        schema.setdefault(table, {})[field] = {
            "type": ftype.strip(),
            "options": [],
            "foreign_key": fk,
            # Store layout as coordinate dict
            "layout": {
                "leftPct":  left_pct,
                "widthPct": width_pct,
                "topEm":    top_em,
                "heightEm": height_em
            }
        }
        # Parse options if present
        if options:
            try:
                schema[table][field]["options"] = json.loads(options)
            except Exception:
                schema[table][field]["options"] = []
    conn.close()
    return schema


# Initialize in-memory cache
try:
    FIELD_SCHEMA = load_field_schema()
except Exception as e:
    print(f"Error loading FIELD_SCHEMA: {e}")


def update_foreign_field_options():
    # For each 'foreign_key' field, fetch id+label from its foreign table and update field_options.
    # Local import to avoid circular dependency
    from db.validation import validate_table

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Step 1: Get all foreign key definitions
    cur.execute("""
        SELECT table_name, field_name, field_type, foreign_key
        FROM field_schema
        WHERE field_type = 'foreign_key'
    """)
    rows = cur.fetchall()

    for table_name, field_name, field_type, foreign_table in rows:
        if not foreign_table:
            continue
        # Validate the foreign table
        try:
            validate_table(foreign_table)
        except ValueError as e:
            print(f"Skipping {table_name}.{field_name}: invalid table {foreign_table} ({e})")
            continue
        # Step 2: Inspect foreign table columns
        try:
            cur.execute(f"PRAGMA table_info({foreign_table})")
            cols = [r[1] for r in cur.fetchall()]
            if not cols:
                raise ValueError(f"No columns in {foreign_table}")
            label_field = cols[1] if len(cols) > 1 else cols[0]
            if label_field not in cols:
                continue
            # Step 3: Fetch id, label pairs
            cur.execute(f"SELECT id, {label_field} FROM {foreign_table}")
            options = [r[1] for r in cur.fetchall()]
        except Exception as e:
            print(f"Skipping {table_name}.{field_name} → {foreign_table}: {e}")
            continue
        # Step 4: Update field_options JSON
        cur.execute("""
            UPDATE field_schema
            SET field_options = ?
            WHERE table_name = ? AND field_name = ?
        """, (json.dumps(options), table_name, field_name))

    conn.commit()
    conn.close()


def get_field_schema():
    return FIELD_SCHEMA

def load_core_tables(conn):
    row = conn.execute(
        "SELECT value FROM config WHERE key = ?", ("core_tables",)
    ).fetchone()
    return [t.strip() for t in row[0].split(",")] if row else []
