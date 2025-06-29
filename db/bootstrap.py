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
        1,
    ),
    (
        "handler_type",
        "rotating",
        "general",
        "select",
        ["rotating", "timed", "stream"],
        0,
    ),
    ("max_file_size", 5242880, "general", "integer", 0),
    ("backup_count", 3, "general", "integer", 0),
    ("when_interval", "midnight", "general", "string", 0),
    ("interval_count", 1, "general", "integer", 0),
    (
        "log_format",
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
        "general",
        "string",
        0,
    ),
    ("filename", "logs/crossbook.log", "general", "string", 0),
    ("heading", "", "home", "string", 1),
    ("relationship_visibility", "{}", "general", "json", 0),
]


def get_layout_defaults() -> dict:
    """Return mapping of field type -> layout width/height defaults."""
    from utils.field_registry import get_type_size_map

    size_map = get_type_size_map()
    return {
        "width": {k: v[0] for k, v in size_map.items()},
        "height": {k: v[1] for k, v in size_map.items()},
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
            "SELECT key, section, type, description, required, options, wizard FROM config"
        )
        for key, section, type_, desc, req, opts, wiz in src_cur.fetchall():
            cur.execute("SELECT 1 FROM config WHERE key = ?", (key,))
            if cur.fetchone():
                cur.execute(
                    "UPDATE config SET section=?, type=?, description=?, required=?, options=?, wizard=? WHERE key=?",
                    (section, type_, desc, req, opts, wiz, key),
                )
            else:
                cur.execute(
                    "INSERT INTO config (key, value, section, type, description, required, options, wizard) VALUES (?, '', ?, ?, ?, ?, ?, ?)",
                    (key, section, type_, desc, req, opts, wiz),
                )


def ensure_relationships_table(path: str) -> None:
    """Ensure the relationships table exists."""
    with sqlite3.connect(path) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='relationships'"
        )
        exists = cur.fetchone() is not None

        if not exists:
            cur.execute(
                """
                CREATE TABLE relationships (
                    table_a TEXT NOT NULL,
                    id_a INTEGER NOT NULL,
                    table_b TEXT NOT NULL,
                    id_b INTEGER NOT NULL,
                    two_way INTEGER NOT NULL DEFAULT 1,
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
            options TEXT DEFAULT '',
            wizard BOOLEAN DEFAULT 0
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
            row_span INTEGER NOT NULL,
            styling TEXT,
            "group" TEXT DEFAULT 'Dashboard'
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

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS automation_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            table_name TEXT NOT NULL,
            condition_field TEXT NOT NULL,
            condition_operator TEXT NOT NULL,
            condition_value TEXT NOT NULL,
            action_field TEXT NOT NULL,
            action_value TEXT NOT NULL,
            run_on_import BOOLEAN DEFAULT 0,
            schedule TEXT CHECK(schedule IN ('none', 'daily', 'always')) DEFAULT 'none',
            last_run TIMESTAMP,
            run_count INTEGER DEFAULT 0
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
            for cfg in DEFAULT_CONFIGS:
                if len(cfg) == 6:
                    key, value, section, type_, options, wizard = cfg
                    cur.execute(
                        "INSERT INTO config (key, value, section, type, options, wizard) VALUES (?, ?, ?, ?, ?, ?)",
                        (key, str(value), section, type_, json.dumps(options), wizard),
                    )
                elif len(cfg) == 5:
                    key, value, section, type_, wizard = cfg
                    cur.execute(
                        "INSERT INTO config (key, value, section, type, wizard) VALUES (?, ?, ?, ?, ?)",
                        (key, str(value), section, type_, wizard),
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
