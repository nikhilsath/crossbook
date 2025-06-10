from datetime import datetime
from db.database import get_connection


def get_config_rows():
    """Return all configuration rows with metadata."""

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT key, value, section, type, description, date_updated FROM config"
    )
    rows = cur.fetchall()
    conn.close()

    columns = ["key", "value", "section", "type", "description", "date_updated"]
    return [dict(zip(columns, row)) for row in rows]


def get_logging_config():
    """Return logging-related configuration values from the database."""

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT key, value FROM config WHERE section = 'logging'")
    rows = cur.fetchall()

    conn.close()

    config = {}
    for key, val in rows:
        config[key] = val

    return config


def get_all_config():
    """Return the entire config table as a simple key/value dict."""

    return {row["key"]: row["value"] for row in get_config_rows()}


def update_config(key: str, value: str) -> int:
    """Update a configuration value and timestamp."""

    conn = get_connection()
    cur = conn.cursor()
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute(
        "UPDATE config SET value = ?, date_updated = ? WHERE key = ?",
        (value, timestamp, key),
    )
    conn.commit()
    affected = cur.rowcount
    conn.close()
    return affected

