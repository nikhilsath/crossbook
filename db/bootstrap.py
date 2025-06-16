import os
import sqlite3
import json

# Default configuration settings used by the setup wizard
DEFAULT_CONFIGS = [
    (
        "log_level",
        "INFO",
        "general",
        "select",
        ["DEBUG", "INFO", "WARNING", "ERROR"],
    ),
    (
        "handler_type",
        "rotating",
        "general",
        "select",
        ["rotating", "timed", "stream"],
    ),
    ("max_file_size", 5242880, "general", "integer"),
    ("backup_count", 3, "general", "integer"),
    ("when_interval", "midnight", "general", "string"),
    ("interval_count", 1, "general", "integer"),
    (
        "log_format",
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        "general",
        "string",
    ),
    ("filename", "logs/crossbook.log", "general", "string"),
    ("heading", "", "home", "string"),
    ("relationship_visibility", "{}", "general", "json"),
]

LAYOUT_DEFAULTS = {
    "width": {
        "textarea": 12,
        "select": 5,
        "text": 12,
        "foreign_key": 5,
        "boolean": 3,
        "number": 4,
        "multi_select": 6,
    },
    "height": {
        "textarea": 18,
        "select": 4,
        "text": 4,
        "foreign_key": 10,
        "boolean": 7,
        "number": 3,
        "multi_select": 8,
    },
}


def _copy_config_metadata(cur: sqlite3.Cursor, dest_path: str) -> None:
    """Copy config metadata from the default database."""
    from db.database import DEFAULT_DB_PATH

    src_path = os.path.abspath(DEFAULT_DB_PATH)
    dest_path = os.path.abspath(dest_path)
    if src_path == dest_path or not os.path.exists(src_path):
        return

    with sqlite3.connect(src_path) as src_conn:
        src_cur = src_conn.cursor()
        src_cur.execute(
            "SELECT key, section, type, description, required, options FROM config"
        )
        for key, section, type_, desc, req, opts in src_cur.fetchall():
            cur.execute("SELECT 1 FROM config WHERE key = ?", (key,))
            if cur.fetchone():
                cur.execute(
                    "UPDATE config SET section=?, type=?, description=?, required=?, options=? WHERE key=?",
                    (section, type_, desc, req, opts, key),
                )
            else:
                cur.execute(
                    "INSERT INTO config (key, value, section, type, description, required, options) VALUES (?, '', ?, ?, ?, ?, ?)",
                    (key, section, type_, desc, req, opts),
                )


def ensure_relationships_table(path: str) -> None:
    """Create the relationships table if it doesn't exist."""
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='relationships'"
        )
        if cur.fetchone():
            return
        cur.execute(
            """
            CREATE TABLE relationships (
                table_a TEXT NOT NULL,
                id_a INTEGER NOT NULL,
                table_b TEXT NOT NULL,
                id_b INTEGER NOT NULL,
                UNIQUE (table_a, id_a, table_b, id_b)
            )
            """
        )
        cur.execute(
            "CREATE INDEX idx_relationships_a ON relationships (table_a, id_a)"
        )
        cur.execute(
            "CREATE INDEX idx_relationships_b ON relationships (table_b, id_b)"
        )
        conn.commit()


def _create_core_tables(cur: sqlite3.Cursor) -> None:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            section TEXT DEFAULT 'general',
            type TEXT DEFAULT 'string',
            description TEXT DEFAULT '',
            date_updated TEXT,
            required BOOLEAN DEFAULT 0,
            labels TEXT DEFAULT '',
            options TEXT DEFAULT ''
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS config_base_tables (
            table_name TEXT PRIMARY KEY,
            display_name TEXT,
            description TEXT,
            sort_order INTEGER
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS field_schema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            field_name TEXT NOT NULL,
            field_type TEXT NOT NULL,
            field_options TEXT,
            foreign_key TEXT,
            col_start INTEGER NOT NULL DEFAULT 0,
            col_span INTEGER NOT NULL DEFAULT 0,
            row_start INTEGER NOT NULL DEFAULT 0,
            row_span INTEGER NOT NULL DEFAULT 0,
            styling TEXT
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS dashboard_widget (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            widget_type TEXT NOT NULL,
            col_start INTEGER NOT NULL,
            col_span INTEGER NOT NULL,
            row_start INTEGER NOT NULL,
            row_span INTEGER NOT NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS edit_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            record_id INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            field_name TEXT,
            old_value TEXT,
            new_value TEXT,
            actor TEXT
        )
        """
    )

    # Generic relationships table for many-to-many links
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS relationships (
            table_a TEXT NOT NULL,
            id_a INTEGER NOT NULL,
            table_b TEXT NOT NULL,
            id_b INTEGER NOT NULL,
            UNIQUE (table_a, id_a, table_b, id_b)
        )
        """
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_relationships_a ON relationships (table_a, id_a)"
    )
    cur.execute(
        "CREATE INDEX IF NOT EXISTS idx_relationships_b ON relationships (table_b, id_b)"
    )


def ensure_default_configs(path: str) -> None:
    """Insert DEFAULT_CONFIGS into the config table if it is empty."""
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM config")
        count = cur.fetchone()[0]
        if count == 0:
            for cfg in DEFAULT_CONFIGS:
                if len(cfg) == 5:
                    key, value, section, type_, options = cfg
                    cur.execute(
                        "INSERT INTO config (key, value, section, type, options) VALUES (?, ?, ?, ?, ?)",
                        (key, str(value), section, type_, json.dumps(options)),
                    )
                else:
                    key, value, section, type_ = cfg
                    cur.execute(
                        "INSERT INTO config (key, value, section, type) VALUES (?, ?, ?, ?)",
                        (key, str(value), section, type_),
                    )
            conn.commit()

        _copy_config_metadata(cur, path)
        ensure_relationships_table(path)

def initialize_database(path: str) -> None:
    """Create a new database with core tables."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        _create_core_tables(cur)
        conn.commit()
    ensure_relationships_table(path)

