import datetime
import logging
from typing import Any, Dict, List, Optional
from db.database import get_connection

logger = logging.getLogger(__name__)

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS automation_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    table_name TEXT NOT NULL,
    condition_field TEXT NOT NULL,
    condition_operator TEXT NOT NULL,
    condition_value TEXT,
    action_field TEXT NOT NULL,
    action_value TEXT,
    run_on_import BOOLEAN NOT NULL DEFAULT 0,
    schedule TEXT NOT NULL DEFAULT 'none',
    last_run TEXT,
    run_count INTEGER NOT NULL DEFAULT 0
)
"""


def _ensure_table() -> None:
    with get_connection() as conn:
        conn.execute(CREATE_SQL)
        conn.commit()


def create_rule(rule: Dict[str, Any]) -> Optional[int]:
    """Insert a new automation rule and return its id."""
    _ensure_table()
    fields = [
        "name",
        "table_name",
        "condition_field",
        "condition_operator",
        "condition_value",
        "action_field",
        "action_value",
        "run_on_import",
        "schedule",
    ]
    values = [rule.get(f) for f in fields]
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO automation_rules
            (name, table_name, condition_field, condition_operator,
             condition_value, action_field, action_value, run_on_import, schedule)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )
        conn.commit()
        return cur.lastrowid


def update_rule(rule_id: int, **fields: Any) -> int:
    """Update an existing rule. Returns rows affected."""
    _ensure_table()
    if not fields:
        return 0
    sets = ", ".join(f"{k} = ?" for k in fields)
    params = list(fields.values()) + [rule_id]
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"UPDATE automation_rules SET {sets} WHERE id = ?", params)
        conn.commit()
        return cur.rowcount


def delete_rule(rule_id: int) -> int:
    _ensure_table()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM automation_rules WHERE id = ?", (rule_id,))
        conn.commit()
        return cur.rowcount


def get_rules(table_name: str | None = None, rule_id: int | None = None) -> List[Dict[str, Any]]:
    _ensure_table()
    query = (
        "SELECT id, name, table_name, condition_field, condition_operator,"
        " condition_value, action_field, action_value, run_on_import, schedule,"
        " last_run, run_count FROM automation_rules"
    )
    params: List[Any] = []
    clauses = []
    if table_name:
        clauses.append("table_name = ?")
        params.append(table_name)
    if rule_id:
        clauses.append("id = ?")
        params.append(rule_id)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]


def increment_run_count(rule_id: int) -> None:
    _ensure_table()
    ts = datetime.datetime.utcnow().isoformat(timespec="seconds")
    with get_connection() as conn:
        conn.execute(
            "UPDATE automation_rules SET run_count = COALESCE(run_count,0)+1, last_run=? WHERE id=?",
            (ts, rule_id),
        )
        conn.commit()


def reset_run_count(rule_id: int | None = None) -> None:
    _ensure_table()
    with get_connection() as conn:
        if rule_id is None:
            conn.execute("UPDATE automation_rules SET run_count = 0")
        else:
            conn.execute("UPDATE automation_rules SET run_count = 0 WHERE id = ?", (rule_id,))
        conn.commit()


def get_rule_logs(rule_id: int, limit: int = 20) -> List[Dict[str, Any]]:
    actor = f"rule:{rule_id}"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, table_name, record_id, field_name, old_value, new_value, timestamp "
            "FROM edit_history WHERE actor = ? ORDER BY id DESC LIMIT ?",
            (actor, limit),
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]

