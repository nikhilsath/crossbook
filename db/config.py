from datetime import datetime
from db.database import get_connection


def get_logging_config():
    """Return logging-related configuration values from the database."""

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM config WHERE key LIKE 'logging.%'")
    rows = cur.fetchall()
    conn.close()

    config = {}
    for full_key, val in rows:
        # full_key is like 'logging.log_level'; we want 'log_level'
        subkey = full_key.split('.', 1)[1]
        config[subkey] = val
    return config


def get_all_config():
    """Return the entire config table as a simple key/value dict."""

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM config")
    rows = cur.fetchall()
    conn.close()

    return {key: val for key, val in rows}


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

