import logging
from flask import request, jsonify
from db.automation import (
    create_rule,
    update_rule,
    delete_rule,
    get_rules,
    reset_run_count,
)
from automation.engine import run_rule
from db.database import get_connection
from db.edit_history import get_edit_entry, revert_edit
from . import admin_bp

logger = logging.getLogger(__name__)


@admin_bp.route('/admin/api/automation/rules')
def list_rules():
    return jsonify(get_rules())


@admin_bp.route('/admin/api/automation/rules', methods=['POST'])
def create_rule_route():
    data = request.get_json(silent=True) or {}
    rule_id = create_rule(
        data.get('name', ''),
        data.get('table_name', ''),
        data.get('condition_field', ''),
        data.get('condition_operator', 'equals'),
        data.get('condition_value', ''),
        data.get('action_field', ''),
        data.get('action_value', ''),
        bool(data.get('run_on_import')),
        data.get('schedule', 'none'),
    )
    return jsonify({'id': rule_id})


@admin_bp.route('/admin/api/automation/rules/<int:rule_id>', methods=['POST'])
def update_rule_route(rule_id):
    data = request.get_json(silent=True) or {}
    update_rule(rule_id, **data)
    return jsonify({'success': True})


@admin_bp.route('/admin/api/automation/rules/<int:rule_id>/delete', methods=['POST'])
def delete_rule_route(rule_id):
    delete_rule(rule_id)
    return jsonify({'success': True})


@admin_bp.route('/admin/api/automation/rules/<int:rule_id>/run', methods=['POST'])
def run_rule_route(rule_id):
    count = run_rule(rule_id)
    return jsonify({'updated': count})


@admin_bp.route('/admin/api/automation/rules/<int:rule_id>/reset', methods=['POST'])
def reset_rule_route(rule_id):
    reset_run_count(rule_id)
    return jsonify({'success': True})


@admin_bp.route('/admin/api/automation/rules/<int:rule_id>/logs')
def rule_logs(rule_id):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, table_name, record_id, timestamp, field_name, old_value, new_value, actor "
            "FROM edit_history WHERE actor = ? ORDER BY id DESC LIMIT 20",
            (f'rule:{rule_id}',),
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return jsonify([dict(zip(cols, r)) for r in rows])


@admin_bp.route('/admin/api/automation/rollback', methods=['POST'])
def rollback_entry():
    data = request.get_json(silent=True) or {}
    entry_id = int(data.get('entry_id', 0))
    entry = get_edit_entry(entry_id)
    if not entry:
        return jsonify({'error': 'not_found'}), 404
    revert_edit(entry)
    return jsonify({'success': True})
