import sqlite3
import os

# Resolve the SQLite database path relative to this file so the
# application can be executed from any working directory.
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "crossbook.db")

def get_connection():
    """Return a connection to the project database."""
    return sqlite3.connect(DB_PATH)
