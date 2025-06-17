import logging
from huey import crontab
from imports.tasks import huey
from db.automation import get_rules, increment_run_count
from db.records import get_all_records, get_record_by_id, update_field_value
from db.schema import get_field_schema
from utils.record_ops import _normalize_value
from db.edit_history import append_edit_log

logger = logging.getLogger(__name__)

@huey.task()
def run_rule(rule_id: int) -> dict | None:
    rules = get_rules(rule_id=rule_id)
    if not rules:
        logger.warning("run_rule: rule %s not found", rule_id)
        return None
    rule = rules[0]
    table = rule["table_name"]
    cond_field = rule["condition_field"]
    cond_value = rule.get("condition_value")
    op = rule.get("condition_operator", "equals")
    act_field = rule["action_field"]
    act_value = rule.get("action_value")
    records = get_all_records(table, filters={cond_field: cond_value}, ops={cond_field: op})
    ids = [r.get("id") for r in records if r.get("id") is not None]
    schema = get_field_schema().get(table, {})
    fmeta = schema.get(act_field, {})
    norm_val = _normalize_value(fmeta.get("type", "text"), act_value)
    for rid in ids:
        prev = get_record_by_id(table, rid)
        old = prev.get(act_field) if prev else None
        if update_field_value(table, rid, act_field, norm_val):
            append_edit_log(
                table,
                rid,
                act_field,
                old,
                norm_val,
                actor=f"rule:{rule_id}",
            )
    increment_run_count(rule_id)
    return {"updated": len(ids)}


@huey.periodic_task(crontab(minute="*/10"))
def run_always_rules() -> None:
    for rule in get_rules():
        if rule.get("schedule") == "always":
            run_rule(rule["id"])  # type: ignore[arg-type]


@huey.periodic_task(crontab(hour=0, minute=0))
def run_daily_rules() -> None:
    for rule in get_rules():
        if rule.get("schedule") == "daily":
            run_rule(rule["id"])  # type: ignore[arg-type]

