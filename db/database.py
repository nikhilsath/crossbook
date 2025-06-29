import sqlite3
import re
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "crossbook.db")

from contextlib import contextmanager

try:
    _test = sqlite3.connect(":memory:")
    _test.create_function("REGEXP", 2, lambda p, v: 1)
    _test.execute("SELECT 'a' REGEXP 'a'")
    _test.close()
    SUPPORTS_REGEX = True
except Exception:
    SUPPORTS_REGEX = False

DB_PATH = os.path.abspath(DEFAULT_DB_PATH)


def init_db_path(path: str | None = None) -> None:
    """Set DB_PATH from an argument or the DB config table."""
    global DB_PATH
    if path:
        DB_PATH = os.path.abspath(path)
        return

    DB_PATH = os.path.abspath(DEFAULT_DB_PATH)

    try:
        from db.config import get_config_rows

        rows = get_config_rows("database")
        cfg = {row["key"]: row["value"] for row in rows}
        cfg_path = cfg.get("db_path")
        if cfg_path:
            DB_PATH = os.path.abspath(cfg_path)
    except Exception:
        pass

    try:
        from db.bootstrap import ensure_relationships_table
        ensure_relationships_table(DB_PATH)
    except Exception:
        pass


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


def check_db_status(path: str) -> str:
    """Return 'valid', 'locked', 'corrupted', or 'missing' for a database file."""
    if not path or not os.path.exists(path):
        return 'missing'
    try:
        with sqlite3.connect(path) as conn:
            cur = conn.execute('PRAGMA integrity_check')
            row = cur.fetchone()
            if row and row[0] == 'ok':
                return 'valid'
            return 'corrupted'
    except sqlite3.OperationalError as exc:
        if 'locked' in str(exc).lower():
            return 'locked'
        return 'corrupted'
    except Exception:
        return 'corrupted'
