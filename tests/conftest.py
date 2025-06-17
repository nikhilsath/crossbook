import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from db.database import init_db_path

@pytest.fixture
def client():
    init_db_path('data/crossbook.db')
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
