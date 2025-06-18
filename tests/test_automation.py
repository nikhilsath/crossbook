import os
import sys
import sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from unittest.mock import patch

from main import app
from imports import tasks as import_tasks
from db.automation import create_rule, get_rules, reset_run_count
from db.records import delete_record
from automation import engine

app.testing = True
client = app.test_client()
DB_PATH = 'data/crossbook.db'


def test_rule_runs_on_import():
    import_tasks.huey.immediate = True
    engine.huey.immediate = True
    rule_id = create_rule(
        'AutoDesc',
        'character',
        'character',
        'equals',
        'AutoTest',
        'description',
        'RULED',
        True,
        'none',
    )
    from db.records import create_record
    rec_id = create_record('character', {'character': 'AutoTest', 'description': 'orig'})
    engine.run_import_rules('character')
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT description FROM character WHERE id=?", (rec_id,)).fetchone()
        assert row is not None
        desc = row[0]
    assert desc == 'RULED'
    delete_record('character', rec_id)
    reset_run_count(rule_id)

def test_run_count_reset():
    engine.huey.immediate = True
    rule_id = create_rule(
        'CountRule',
        'character',
        'character',
        'equals',
        'Ajihad',
        'description',
        'X',
        False,
        'none',
    )
    engine.run_rule(rule_id)
    rules = [r for r in get_rules() if r['id'] == rule_id]
    assert rules[0]['run_count'] >= 1
    reset_run_count(rule_id)
    rules = [r for r in get_rules() if r['id'] == rule_id]
    assert rules[0]['run_count'] == 0
from unittest.mock import patch


def test_trigger_scheduled_rules_enqueues_only_eligible_tasks():
    engine.huey.immediate = True
    rules = [
        {"id": 1, "schedule": "daily"},
        {"id": 2, "schedule": "always"},
        {"id": 3, "schedule": "weekly"},
        {"id": 4, "schedule": "none"},
    ]
    original_enqueue = engine.huey.enqueue
    with patch('automation.engine.get_rules', return_value=rules), \
         patch('automation.engine.run_rule', return_value=0) as run_rule_mock, \
         patch.object(engine.huey, 'enqueue') as enqueue_mock:
        enqueue_mock.side_effect = original_enqueue
        engine.trigger_scheduled_rules()
        assert run_rule_mock.call_count == 2
        assert enqueue_mock.call_count == 2
        called_ids = [call.args[0].args[0] for call in enqueue_mock.call_args_list]
        assert set(called_ids) == {1, 2}
