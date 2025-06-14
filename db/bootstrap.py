import os
import sqlite3
import json

# Default configuration settings used by the setup wizard
DEFAULT_CONFIGS = [
    ("log_level", "INFO", "general", "string"),
    ("handler_type", "rotating", "general", "string"),
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


def ensure_default_configs(path: str) -> None:
    """Insert DEFAULT_CONFIGS into the config table if it is empty."""
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM config")
        count = cur.fetchone()[0]
        if count == 0:
            for key, value, section, type_ in DEFAULT_CONFIGS:
                cur.execute(
                    "INSERT INTO config (key, value, section, type) VALUES (?, ?, ?, ?)",
                    (key, str(value), section, type_),
                )
            conn.commit()


def initialize_database(path: str) -> None:
    """Create a new database with core tables."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        _create_core_tables(cur)
        # Default records are no longer inserted
        conn.commit()

