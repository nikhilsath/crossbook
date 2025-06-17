import os
import sys
import sqlite3
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.database import init_db_path
from db.records import get_record_by_id, create_record
from db.automation import (
    create_rule,
    get_rules,
    reset_run_count,
    get_rule_logs,
)
from automation.engine import run_rule, run_daily_rules
from imports import tasks as import_tasks

DB_PATH = 'data/crossbook.db'
init_db_path(DB_PATH)


def test_rule_creation_and_reset():
    rule_id = create_rule({
        'name': 'test',
        'table_name': 'location',
        'condition_field': 'location',
        'condition_operator': 'equals',
        'condition_value': 'XPlace',
        'action_field': 'description',
        'action_value': 'AUTO',
        'run_on_import': 1,
        'schedule': 'none',
    })
    rules = get_rules(rule_id=rule_id)
    assert rules and rules[0]['name'] == 'test'
    reset_run_count(rule_id)
    assert get_rules(rule_id=rule_id)[0]['run_count'] == 0


def test_rule_executes_on_import():
    import_tasks.huey.immediate = True
    rule_id = create_rule({
        'name': 'import_rule',
        'table_name': 'location',
        'condition_field': 'location',
        'condition_operator': 'equals',
        'condition_value': 'ImportPlace',
        'action_field': 'description',
        'action_value': 'IMPORTED',
        'run_on_import': 1,
        'schedule': 'none',
    })
    import_tasks.import_rows('location', [{'location': 'ImportPlace', 'description': ''}])
    with sqlite3.connect(DB_PATH) as conn:
        status = conn.execute("SELECT description FROM location WHERE location='ImportPlace'").fetchone()[0]
    assert status == 'IMPORTED'
    assert get_rules(rule_id=rule_id)[0]['run_count'] == 1


def test_daily_schedule_and_rollback():
    import_tasks.huey.immediate = True
    rule_id = create_rule({
        'name': 'daily_rule',
        'table_name': 'location',
        'condition_field': 'location',
        'condition_operator': 'equals',
        'condition_value': 'DailyPlace',
        'action_field': 'description',
        'action_value': 'DAILY',
        'run_on_import': 0,
        'schedule': 'daily',
    })
    rec_id = create_record('location', {'location': 'DailyPlace'})
    run_daily_rules()
    assert get_record_by_id('location', rec_id)['description'] == 'DAILY'
    logs = get_rule_logs(rule_id, limit=1)
    assert logs
    from db.edit_history import revert_edit
    assert revert_edit(logs[0])
    assert get_record_by_id('location', rec_id)['description'] != 'DAILY'
    reset_run_count(rule_id)

