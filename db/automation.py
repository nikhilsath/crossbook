import logging
from db.database import get_connection

logger = logging.getLogger(__name__)


def create_rule(
    name: str,
    table_name: str,
    condition_field: str,
    condition_operator: str,
    condition_value: str,
    action_field: str,
    action_value: str,
    run_on_import: bool = False,
    schedule: str = "none",
) -> int:
    """Insert a new automation rule and return its id."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO automation_rules
                (name, table_name, condition_field, condition_operator,
                 condition_value, action_field, action_value,
                 run_on_import, schedule)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                table_name,
                condition_field,
                condition_operator,
                condition_value,
                action_field,
                action_value,
                int(run_on_import),
                schedule,
            ),
        )
        rule_id = cur.lastrowid
        conn.commit()
    logger.info(
        "Created automation rule %s (id=%s) for table %s",
        name,
        rule_id,
        table_name,
    )
    return rule_id


def update_rule(rule_id: int, **updates) -> bool:
    """Update fields for an automation rule."""
    if not updates:
        return False
    fields = ", ".join(f"{k}=?" for k in updates)
    params = list(updates.values()) + [rule_id]
    with get_connection() as conn:
        conn.execute(
            f"UPDATE automation_rules SET {fields} WHERE id = ?",
            params,
        )
        conn.commit()
    logger.info("Updated automation rule %s with %s", rule_id, updates)
    return True


def delete_rule(rule_id: int) -> bool:
    with get_connection() as conn:
        conn.execute("DELETE FROM automation_rules WHERE id = ?", (rule_id,))
        conn.commit()
    logger.info("Deleted automation rule %s", rule_id)
    return True


def get_rules(table_name: str | None = None) -> list[dict]:
    """Return automation rules optionally filtered by table."""
    logger.debug("Fetching rules for table %s", table_name)
    with get_connection() as conn:
        cur = conn.cursor()
        if table_name:
            cur.execute(
                "SELECT * FROM automation_rules WHERE table_name = ?",
                (table_name,),
            )
        else:
            cur.execute("SELECT * FROM automation_rules")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]


def increment_run_count(rule_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE automation_rules SET run_count = COALESCE(run_count,0)+1, "
            "last_run = datetime('now') WHERE id = ?",
            (rule_id,),
        )
        conn.commit()
    logger.debug("Incremented run count for rule %s", rule_id)


def reset_run_count(rule_id: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE automation_rules SET run_count = 0 WHERE id = ?",
            (rule_id,),
        )
        conn.commit()
    logger.info("Reset run count for rule %s", rule_id)
