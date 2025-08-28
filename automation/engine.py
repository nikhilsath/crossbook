import logging
from db.database import get_connection
from db.records import update_field_value
from db.edit_history import append_edit_log
from db.automation import get_rules, increment_run_count
from imports.tasks import huey

logger = logging.getLogger(__name__)


def run_rule(rule_id: int) -> int:
    """Execute a single automation rule. Returns number of records updated."""
    rules = [r for r in get_rules() if r["id"] == rule_id]
    if not rules:
        logger.info("Rule %s not found", rule_id)
        return 0
    rule = rules[0]
    table = rule["table_name"]
    condition_field = rule["condition_field"]
    condition_value = rule["condition_value"]
    operator = rule["condition_operator"]
    action_field = rule["action_field"]
    action_value = rule["action_value"]

    sql_op = "=" if operator == "equals" else "LIKE"
    param = condition_value if operator == "equals" else f"%{condition_value}%"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            f"SELECT id, {action_field} FROM {table} WHERE {condition_field} {sql_op} ?",
            (param,),
        )
        rows = cur.fetchall()
    count = 0
    for rec_id, old_val in rows:
        if update_field_value(table, rec_id, action_field, action_value):
            append_edit_log(
                table,
                rec_id,
                action_field,
                old_val,
                action_value,
                actor=f"rule:{rule_id}",
            )
            count += 1
    if rows:
        increment_run_count(rule_id)
    return count


@huey.task()
def run_rule_task(rule_id: int) -> int:
    return run_rule(rule_id)


def run_import_rules(table_name: str) -> None:
    for rule in get_rules(table_name):
        if rule.get("run_on_import"):
            run_rule(rule["id"])


def trigger_scheduled_rules() -> None:
    for rule in get_rules():
        if rule.get("schedule") in {"daily", "always"}:
            task = run_rule_task.s(rule["id"])
            huey.enqueue(task)
