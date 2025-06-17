import logging
from flask import render_template, jsonify, request
from . import admin_bp
from db.automation import (
    create_rule,
    update_rule,
    delete_rule,
    get_rules,
    reset_run_count,
    get_rule_logs,
)
from db.edit_history import get_edit_entry, revert_edit
from automation.engine import run_rule

logger = logging.getLogger(__name__)


@admin_bp.route("/admin/automation")
def automation_page():
    return render_template("admin/admin_automation.html")


@admin_bp.route("/admin/automation/rules")
def automation_list():
    table = request.args.get("table")
    rules = get_rules(table_name=table)
    return jsonify(rules)


@admin_bp.route("/admin/automation/rule", methods=["POST"])
def automation_create():
    data = request.get_json(silent=True) or {}
    rid = create_rule(data)
    return jsonify({"id": rid})


@admin_bp.route("/admin/automation/rule/<int:rule_id>", methods=["POST"])
def automation_update(rule_id):
    data = request.get_json(silent=True) or {}
    update_rule(rule_id, **data)
    return jsonify({"success": True})


@admin_bp.route("/admin/automation/rule/<int:rule_id>", methods=["DELETE"])
def automation_delete(rule_id):
    delete_rule(rule_id)
    return jsonify({"success": True})


@admin_bp.route("/admin/automation/trigger/<int:rule_id>", methods=["POST"])
def automation_trigger(rule_id):
    run_rule(rule_id)
    return jsonify({"success": True})


@admin_bp.route("/admin/automation/reset/<int:rule_id>", methods=["POST"])
def automation_reset(rule_id):
    reset_run_count(rule_id)
    return jsonify({"success": True})


@admin_bp.route("/admin/automation/logs/<int:rule_id>")
def automation_logs(rule_id):
    try:
        limit = int(request.args.get("limit", 20))
    except (TypeError, ValueError):
        limit = 20
    return jsonify(get_rule_logs(rule_id, limit=limit))


@admin_bp.route("/admin/automation/rollback", methods=["POST"])
def automation_rollback():
    data = request.get_json(silent=True) or {}
    edit_id = data.get("edit_id")
    entry = get_edit_entry(edit_id)
    if not entry:
        return jsonify({"error": "not_found"}), 404
    success = revert_edit(entry)
    return jsonify({"success": bool(success)})

