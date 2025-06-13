import sqlite3
import re
import os
from contextlib import contextmanager

try:
    _test = sqlite3.connect(":memory:")
    _test.create_function("REGEXP", 2, lambda p, v: 1)
    _test.execute("SELECT 'a' REGEXP 'a'")
    _test.close()
    SUPPORTS_REGEX = True
except Exception:
    SUPPORTS_REGEX = False

DB_PATH = os.environ.get("CROSSBOOK_DB_PATH", "data/crossbook.db")


def init_db_path() -> None:
    """Override DB_PATH using database config if available."""
    global DB_PATH
    env_path = os.environ.get("CROSSBOOK_DB_PATH")
    cfg_path = None
    try:
        from db.config import get_database_config

        cfg = get_database_config()
        cfg_path = cfg.get("db_path")
        if cfg_path is None:
            with get_connection() as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO config (key, value, section, type, date_updated) VALUES (?, ?, 'database', 'string', datetime('now'))",
                    ("db_path", DB_PATH),
                )
                conn.commit()
            cfg_path = DB_PATH
    except Exception:
        cfg_path = None

    if env_path:
        DB_PATH = env_path
    elif cfg_path:
        DB_PATH = cfg_path


@contextmanager
def get_connection():
    """Yield a SQLite connection that is automatically closed."""
    conn = sqlite3.connect(DB_PATH)
    if SUPPORTS_REGEX:
        try:
            conn.create_function(
                "REGEXP",
                2,
                lambda pattern, value: 1 if value is not None and re.search(pattern, str(value)) else 0,
            )
        except Exception:
            pass
    try:
        yield conn
    finally:
        conn.close()
