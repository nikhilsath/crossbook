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
               col_start,
               col_span,
               row_start,
               row_span
        FROM field_schema
    """)
    rows = cur.fetchall()
    schema = {}
    for table, field, ftype, options, fk, col_start, col_span, row_start, row_span in rows:
        # Initialize field schema entry
        schema.setdefault(table, {})[field] = {
            "type": ftype.strip(),
            "options": [],
            "foreign_key": fk,
            # Store layout as coordinate dict
            "layout": {
                "colStart":  col_start,
                "colSpan": col_span,
                "rowStart":    row_start,
                "rowSpan": row_span
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

def update_layout(table: str, layout_items: list[dict]) -> int:
    current_schema = load_field_schema()

    if table not in current_schema:
        raise ValueError(f"Unknown table: {table}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    updated = 0

    for item in layout_items:
        field = item.get("field")
        if not field:
            # Skip items without a "field" key
            continue

        # Safely parse numeric layout values (defaults to 0.0)
        try:
            col_start = float(item.get("colStart", 0))
            col_span  = float(item.get("colSpan", 0))
            row_start = float(item.get("rowStart", 0))
            row_span  = float(item.get("rowSpan", 0))
        except (TypeError, ValueError):
            # Skip this item if conversion fails
            continue

        # Perform the SQL UPDATE
        cur.execute(
            """
            UPDATE field_schema
               SET col_start  = ?,
                   col_span   = ?,
                   row_start  = ?,
                   row_span   = ?
             WHERE table_name  = ? AND field_name = ?
            """,
            (col_start, col_span, row_start, row_span, table, field)
        )
        if cur.rowcount:
            updated += 1
            # Also update the in-memory copy immediately
            current_schema[table][field]["layout"] = {
                "colStart": col_start,
                "colSpan":  col_span,
                "rowStart": row_start,
                "rowSpan":  row_span
            }
        # If rowcount == 0, quietly skip (no such field or no change)

    conn.commit()
    conn.close()

    # Refresh the global FIELD_SCHEMA cache
    global FIELD_SCHEMA
    FIELD_SCHEMA = current_schema

    return updated