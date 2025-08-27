import logging
import datetime
import sqlite3
from db.database import get_connection
from db.validation import validate_table

logger = logging.getLogger(__name__)


def append_edit_log(
    table: str,
    record_id: int,
    field_name: str | None,
    old_value: str | None,
    new_value: str | None,
    actor: str | None = None,
) -> None:
    """Insert a row into the edit_history table."""
    validate_table(table)
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            logger.debug(
                "append_edit_log: %s id=%s field=%s old=%r new=%r actor=%r",
                table,
                record_id,
                field_name,
                old_value,
                new_value,
                actor,
            )
            cursor.execute(
                """
                INSERT INTO edit_history
                    (table_name, record_id, timestamp, field_name, old_value, new_value, actor)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (table, record_id, timestamp, field_name, old_value, new_value, actor),
            )
            conn.commit()
            logger.info(
                "Logged edit for %s id=%s field=%s old=%r new=%r",
                table,
                record_id,
                field_name,
                old_value,
                new_value,
            )
        except sqlite3.DatabaseError as e:
            logger.exception("[EDIT LOG ERROR] %s", e)


def get_edit_history(table_name: str, record_id: int, limit: int | None = None) -> list[dict]:
    """Return edit history rows ordered by timestamp descending."""
    validate_table(table_name)

    with get_connection() as conn:
        cur = conn.cursor()
        sql = (
            "SELECT id, table_name, record_id, timestamp, field_name, old_value, new_value, actor "
            "FROM edit_history WHERE table_name = ? AND record_id = ? ORDER BY timestamp DESC"
        )
        params = [table_name, record_id]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        cur.execute(sql, params)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in rows]


def get_edit_entry(edit_id: int) -> dict | None:
    """Return a single edit_history row by id."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, table_name, record_id, timestamp, field_name, old_value, new_value, actor "
            "FROM edit_history WHERE id = ?",
            (edit_id,),
        )
        row = cur.fetchone()
        if row:
            cols = [d[0] for d in cur.description]
            return dict(zip(cols, row))
        return None


def revert_edit(entry: dict) -> bool:
    """Undo the provided edit_history entry."""
    table = entry["table_name"]
    record_id = entry["record_id"]
    field = entry["field_name"]
    old_val = entry["old_value"]
    new_val = entry["new_value"]

    try:
        if not field:
            logger.warning("revert_edit: no field_name provided")
            return False
        if field.startswith("relation_"):
            from db.relationships import add_relationship, remove_relationship

            rel_table = field[len("relation_") :]
            if old_val is None and new_val is not None:
                add_relationship(
                    table, record_id, rel_table, int(new_val), actor="undo"
                )
            elif new_val is None and old_val is not None:
                remove_relationship(
                    table, record_id, rel_table, int(old_val), actor="undo"
                )
            else:
                return False
        else:
            from db.records import update_field_value

            update_field_value(table, record_id, field, old_val)
        if not field.startswith("relation_"):
            append_edit_log(table, record_id, field, new_val, old_val, actor="undo")
    except (sqlite3.DatabaseError, ValueError):
        logger.exception("Failed to revert edit")
        return False
    return True
