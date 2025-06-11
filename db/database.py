import sqlite3
from contextlib import contextmanager

DB_PATH = "data/crossbook.db"


@contextmanager
def get_connection():
    """Yield a SQLite connection that is automatically closed."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()
