import os
import sqlite3

DB_PATH = "data/crossbook.db"

def get_logging_config():

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT key, value FROM config WHERE key LIKE 'logging.%'")
    rows = cur.fetchall()
    conn.close()

    config = {}
    for full_key, val in rows:
        # full_key is like 'logging.log_level'; we want 'log_level'
        subkey = full_key.split(".", 1)[1]
        config[subkey] = val
    return config


def get_config_value(key: str, default=None):
    """Return the configuration value for a given key."""

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT value FROM config WHERE key = ?", (key,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return default
    return row[0]
