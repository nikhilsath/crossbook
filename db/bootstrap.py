import os
import sqlite3

BASE_TABLES = [
    "content",
    "character",
    "thing",
    "faction",
    "location",
    "topic",
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

DEFAULT_CONFIGS = [
    ("log_level", "INFO", "general", "string"),
    ("handler_type", "rotating", "general", "string"),
    ("max_file_size", "5242880", "general", "integer"),
    ("backup_count", "3", "general", "integer"),
    ("when_interval", "midnight", "general", "string"),
    ("interval_count", "1", "general", "integer"),
    (
        "log_format",
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        "general",
        "string",
    ),
    ("filename", "logs/crossbook.log", "general", "string"),
    ("heading", "Load the glass cannons", "home", "string"),
]

DEFAULT_BASE_TABLE_ROWS = [
    ("content", "Content", "Content Index", 1),
    ("character", "Characters", "View all known characters in Alagaesia", 2),
    ("thing", "Things", "Artifacts, tools, and curiosities", 3),
    ("faction", "Factions", "Factions, cultures, and organizations", 4),
    ("location", "Locations", "Important places throughout the land", 5),
    (
        "topic",
        "Lore Topics",
        "Themes, magic systems, and unanswered questions",
        6,
    ),
]

DEFAULT_FIELDS = {
    "content": [
        ("id", "hidden"),
        ("content", "text"),
        ("tags", "multi_select"),
    ],
    "character": [
        ("id", "hidden"),
        ("character", "text"),
    ],
    "thing": [("id", "hidden"), ("thing", "text")],
    "faction": [("id", "hidden"), ("faction", "text")],
    "location": [("id", "hidden"), ("location", "text")],
    "topic": [("id", "hidden"), ("topic", "text")],
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
            date_updated TEXT
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


def _create_base_tables(cur: sqlite3.Cursor) -> None:
    for table in BASE_TABLES:
        cur.execute(
            f"CREATE TABLE IF NOT EXISTS {table} ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT,"
            f" {table} TEXT"
            ")"
        )

    # join tables for many-to-many relationships
    for i in range(len(BASE_TABLES)):
        for j in range(i + 1, len(BASE_TABLES)):
            a, b = sorted([BASE_TABLES[i], BASE_TABLES[j]])
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS {a}_{b} ("
                f"{a}_id INTEGER,"
                f"{b}_id INTEGER,"
                f"UNIQUE({a}_id, {b}_id)"
                ")"
            )


def _insert_defaults(cur: sqlite3.Cursor, path: str) -> None:
    """Insert default rows into the core tables."""
    # Defaults are intentionally omitted so new databases start empty.
    return


def initialize_database(path: str) -> None:
    """Create a new database containing only the core tables."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        _create_core_tables(cur)
        conn.commit()

