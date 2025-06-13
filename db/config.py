from datetime import datetime
from db.database import get_connection
import json


def get_config_rows():
    """Return all configuration rows with metadata."""

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT key, value, section, type, description, date_updated FROM config"
        )
        rows = cur.fetchall()

    columns = ["key", "value", "section", "type", "description", "date_updated"]
    return [dict(zip(columns, row)) for row in rows]


def get_logging_config():
    """Return logging-related configuration values from the database."""

    with get_connection() as conn:
        cur = conn.cursor()

        cur.execute("SELECT key, value FROM config WHERE section = 'logging'")
        rows = cur.fetchall()

    config = {}
    for key, val in rows:
        config[key] = val

    return config


def get_database_config() -> dict:
    """Return database-related configuration values from the database."""

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT key, value FROM config WHERE section = 'database'")
        rows = cur.fetchall()

    config = {}
    for key, val in rows:
        config[key] = val

    return config


def get_all_config():
    """Return the entire config table as a simple key/value dict."""

    return {row["key"]: row["value"] for row in get_config_rows()}


def get_layout_defaults() -> dict:
    """Return layout width/height defaults from the config table."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM config WHERE key = 'layout_defaults'")
        row = cur.fetchone()

    if not row:
        return {}
    try:
        return json.loads(row[0])
    except Exception:
        return {}


def update_config(key: str, value: str) -> int:
    """Update a configuration value and timestamp."""

    with get_connection() as conn:
        cur = conn.cursor()
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            "UPDATE config SET value = ?, date_updated = ? WHERE key = ?",
            (value, timestamp, key),
        )
        if cur.rowcount == 0:
            cur.execute(
                "INSERT INTO config (key, value, date_updated) VALUES (?, ?, ?)",
                (key, value, timestamp),
            )
        conn.commit()
        affected = cur.rowcount

    if key == "db_path":
        # Refresh the global database path so subsequent connections
        # use the newly configured location.
        from db.database import init_db_path

        init_db_path(value)

    return affected

