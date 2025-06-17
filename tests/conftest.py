import os
import sys
import shutil
import pytest

# Ensure repository root is in path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from db.database import init_db_path
from views.admin import reload_app_state

@pytest.fixture
def db_path(tmp_path):
    """Copy the sample database to a temporary location and initialize DB_PATH."""
    src = os.path.join(ROOT_DIR, 'data', 'crossbook.db')
    dst = tmp_path / 'test.db'
    shutil.copy(src, dst)
    init_db_path(str(dst))
    return str(dst)

@pytest.fixture
def app(db_path):
    """Create and configure a new app instance for tests."""
    import main
    flask_app = main.app
    init_db_path(db_path)
    flask_app.testing = True
    with flask_app.app_context():
        reload_app_state()
    return flask_app

@pytest.fixture
def client(app):
    return app.test_client()
