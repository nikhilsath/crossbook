import logging

logger = logging.getLogger(__name__)

from db.database import get_connection
from db.validation import validate_table
from db.records import touch_last_edited
from db.schema import get_title_field


def _get_label(cursor, table, record_id):
    """Return label for a record from the given table."""
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cursor.fetchall()]
    if not cols:
        return None
    title_field = get_title_field(table)
    if title_field:
        label_field = title_field
    elif table in cols:
        label_field = table
    elif len(cols) > 1:
        label_field = cols[1]
    else:
        label_field = cols[0]
    cursor.execute(f"SELECT id, {label_field} FROM {table} WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    return row if row else None


def get_related_records(source_table, record_id):
    """Return dict of related records grouped by table."""
    validate_table(source_table)
    related = {}
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT table_a, id_a, table_b, id_b, two_way
              FROM relationships
             WHERE (table_a = ? AND id_a = ?)
                OR (table_b = ? AND id_b = ?)
            """,
            (source_table, record_id, source_table, record_id),
        )
        links = cur.fetchall()
        for table_a, id_a, table_b, id_b, two_way in links:
            if table_a == source_table and id_a == record_id:
                target_table, target_id = table_b, id_b
            else:
                target_table, target_id = table_a, id_a
            try:
                validate_table(target_table)
            except ValueError:
                continue
            row = _get_label(cur, target_table, target_id)
            if not row:
                continue
            item = {"id": row[0], "name": row[1], "two_way": bool(two_way)}
            # Determine display label for the related table
            row_label = cur.execute(
                "SELECT display_name FROM config_base_tables WHERE table_name = ?",
                (target_table,),
            ).fetchone()
            table_label = row_label[0] if row_label else target_table.capitalize()
            group = related.setdefault(
                target_table,
                {"label": table_label, "items": []},
            )
            group["items"].append(item)
    return related


def add_relationship(
    table_a,
    id_a,
    table_b,
    id_b,
    *,
    actor: str | None = None,
    two_way: bool = True,
):
    validate_table(table_a)
    validate_table(table_b)
    ordered = sorted([(table_a, id_a), (table_b, id_b)], key=lambda t: t[0])
    a_tbl, a_id = ordered[0]
    b_tbl, b_id = ordered[1]
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO relationships (table_a, id_a, table_b, id_b, two_way)"
                " VALUES (?, ?, ?, ?, ?)"
                " ON CONFLICT(table_a,id_a,table_b,id_b) DO UPDATE SET two_way=excluded.two_way",
                (a_tbl, a_id, b_tbl, b_id, 1 if two_way else 0),
            )
            conn.commit()
            success = True
        except Exception as e:
            logger.warning(f"[RELATIONSHIP ADD ERROR] {e}")
            success = False
        if success:
            touch_last_edited(table_a, id_a)
            touch_last_edited(table_b, id_b)
            from db.edit_history import append_edit_log
            append_edit_log(
                table_a,
                id_a,
                f"relation_{table_b}",
                None,
                str(id_b),
                actor=actor,
            )
            append_edit_log(
                table_b,
                id_b,
                f"relation_{table_a}",
                None,
                str(id_a),
                actor=actor,
            )
        return success


def remove_relationship(table_a, id_a, table_b, id_b, *, actor: str | None = None):
    validate_table(table_a)
    validate_table(table_b)
    ordered = sorted([(table_a, id_a), (table_b, id_b)], key=lambda t: t[0])
    a_tbl, a_id = ordered[0]
    b_tbl, b_id = ordered[1]
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(
                "DELETE FROM relationships WHERE table_a = ? AND id_a = ? AND table_b = ? AND id_b = ?",
                (a_tbl, a_id, b_tbl, b_id),
            )
            conn.commit()
            success = True
        except Exception as e:
            logger.warning(f"[RELATIONSHIP REMOVE ERROR] {e}")
            success = False
        if success:
            touch_last_edited(table_a, id_a)
            touch_last_edited(table_b, id_b)
            from db.edit_history import append_edit_log
            append_edit_log(
                table_a,
                id_a,
                f"relation_{table_b}",
                str(id_b),
                None,
                actor=actor,
            )
            append_edit_log(
                table_b,
                id_b,
                f"relation_{table_a}",
                str(id_a),
                None,
                actor=actor,
            )
        return success
