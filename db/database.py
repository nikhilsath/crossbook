import sqlite3
import re
import os

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "crossbook.db")

try:
    from local_settings import CROSSBOOK_DB_PATH as LOCAL_DB_PATH
except Exception:
    LOCAL_DB_PATH = None
from contextlib import contextmanager

try:
    _test = sqlite3.connect(":memory:")
    _test.create_function("REGEXP", 2, lambda p, v: 1)
    _test.execute("SELECT 'a' REGEXP 'a'")
    _test.close()
    SUPPORTS_REGEX = True
except Exception:
    SUPPORTS_REGEX = False

DB_PATH = os.path.abspath(
    os.environ.get("CROSSBOOK_DB_PATH", LOCAL_DB_PATH or DEFAULT_DB_PATH)
)


def init_db_path() -> None:
    """Override DB_PATH using database config if available."""
    global DB_PATH
    env_path = os.environ.get("CROSSBOOK_DB_PATH")
    if env_path:
        env_path = os.path.abspath(env_path)
    local_path = LOCAL_DB_PATH
    if local_path:
        local_path = os.path.abspath(local_path)
    cfg_path = None
    try:
        from db.config import get_database_config

        cfg = get_database_config()
        cfg_path = cfg.get("db_path")
        if cfg_path:
            cfg_path = os.path.abspath(cfg_path)
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
    elif local_path:
        DB_PATH = local_path
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
