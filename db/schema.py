import sqlite3
import json
import logging

logger = logging.getLogger(__name__)

DB_PATH = "data/crossbook.db"
FIELD_SCHEMA = {}

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
    logger.exception("Error loading FIELD_SCHEMA: %s", e)


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
            logger.warning(
                "Skipping %s.%s: invalid table %s (%s)",
                table_name,
                field_name,
                foreign_table,
                e,
            )
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
            logger.warning(
                "Skipping %s.%s → %s: %s",
                table_name,
                field_name,
                foreign_table,
                e,
            )
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

def load_card_info(conn):
    """Return card metadata from the config_base_tables table."""
    rows = conn.execute(
        """
        SELECT table_name, display_name, description
          FROM config_base_tables
         ORDER BY sort_order
        """
    ).fetchall()
    return [
        {
            "table_name": r[0],
            "display_name": r[1],
            "description": r[2],
        }
        for r in rows
    ]


def load_base_tables(conn):
    """Return the list of base table names used by the application."""
    cards = load_card_info(conn)
    return [c["table_name"] for c in cards if c["table_name"] != "dashboard"]

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


def create_base_table(table_name: str, description: str) -> bool:
    """Create a new base table and associated metadata."""
    if not table_name.isidentifier():
        logger.error("Invalid table name: %s", table_name)
        return False

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    try:
        # Ensure the table does not already exist
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        )
        if cur.fetchone():
            logger.error("Table %s already exists", table_name)
            return False

        # Create the base table
        cur.execute(
            f"""
            CREATE TABLE {table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                {table_name} TEXT
            )
            """
        )

        # Always ensure the edit_log column exists
        try:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN edit_log TEXT")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" not in str(exc).lower():
                raise

        # Insert default field schema rows
        defaults = [
            (table_name, "id", "hidden", None, None, 0, 0, 0, 0),
            (table_name, table_name, "text", None, None, 0, 0, 0, 0),
            (table_name, "edit_log", "hidden", None, None, 0, 0, 0, 0),
        ]
        cur.executemany(
            """
            INSERT OR IGNORE INTO field_schema
              (table_name, field_name, field_type, field_options, foreign_key,
               col_start, col_span, row_start, row_span)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            defaults,
        )

        # Determine next sort_order value
        cur.execute("SELECT COALESCE(MAX(sort_order), 0) + 1 FROM config_base_tables")
        next_order = cur.fetchone()[0]

        # Insert into config_base_tables
        cur.execute(
            """
            INSERT INTO config_base_tables
              (table_name, display_name, description, sort_order)
            VALUES (?, ?, ?, ?)
            """,
            (table_name, table_name, description, next_order),
        )

        # Build join tables against existing base tables (excluding the new one)
        cur.execute(
            "SELECT table_name FROM config_base_tables WHERE table_name != ?",
            (table_name,),
        )
        existing = [r[0] for r in cur.fetchall()]
        for other in existing:
            a, b = sorted([table_name, other])
            join_table = f"{a}_{b}"
            first = f"{a}_id"
            second = f"{b}_id"
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {join_table} (
                    {first} INTEGER,
                    {second} INTEGER,
                    UNIQUE({first}, {second})
                )
                """
            )

        conn.commit()
    except Exception as exc:
        logger.exception("Error creating base table %s: %s", table_name, exc)
        conn.rollback()
        return False
    finally:
        conn.close()

    # Refresh the in-memory FIELD_SCHEMA cache
    global FIELD_SCHEMA
    FIELD_SCHEMA = load_field_schema()

    return True
