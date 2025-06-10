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

    # Newer databases store logging keys without the "logging." prefix and use
    # the section column for grouping. Look for those first.
    cur.execute("SELECT key, value FROM config WHERE section = 'logging'")
    rows = cur.fetchall()

    # Fall back to the old key scheme where each key started with "logging.".
    if not rows:
        cur.execute("SELECT key, value FROM config WHERE key LIKE 'logging.%'")
        rows = cur.fetchall()

    conn.close()

    config = {}
    for full_key, val in rows:
        # Older keys may still contain the 'logging.' prefix; strip it if present
        subkey = full_key.split('.', 1)[-1]
        config[subkey] = val

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

