import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app
from db.database import init_db_path
from utils.records_helpers import parse_list_params

init_db_path('data/crossbook.db')
app.testing = True


def test_parse_list_params_basic():
    query = '/?search=test&RACE=Elf&race_op=equals&notes_mode=all&sort=character&dir=desc&extra=1'
    with app.test_request_context(query):
        params = parse_list_params('character')
    assert params['search'] == 'test'
    assert params['filters'] == {'race': ['Elf']}
    assert params['ops'] == {'race': 'equals'}
    assert params['modes'] == {'notes': 'all'}
    assert params['sort_field'] == 'character'
    assert params['direction'] == 'desc'
    assert 'extra' not in params['filters']
