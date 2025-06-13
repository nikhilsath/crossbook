import os
import sqlite3
import json

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


def _insert_defaults(cur: sqlite3.Cursor, path: str, include_base_tables: bool = True) -> None:
    """Previously inserted sample data; now intentionally left blank."""
    return


def initialize_database(path: str, include_base_tables: bool = False) -> None:
    """Create a new database with core tables."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        _create_core_tables(cur)
        if include_base_tables:
            _create_base_tables(cur)
        # Default records are no longer inserted
        conn.commit()

