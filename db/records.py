import logging

logger = logging.getLogger(__name__)
import datetime
from db.database import get_connection
from db.schema import get_field_schema
from db.validation import validate_table, validate_fields, validate_field



def _build_filters(table, search=None, filters=None, ops=None):
    """Return SQL where clauses and params for the provided filters/search."""
    clauses = []
    params = []

    if filters:
        validate_fields(table, filters.keys())
        for fld, val in filters.items():
            values = val if isinstance(val, list) else [val]
            clean_values = [v for v in values if v != ""]
            if not clean_values:
                continue
            op = (ops or {}).get(fld, "contains")
            field_clauses = []
            for v in clean_values:
                if op == "equals":
                    field_clauses.append(f"{fld} = ?")
                    params.append(v)
                elif op == "starts_with":
                    field_clauses.append(f"{fld} LIKE ?")
                    params.append(f"{v}%")
                elif op == "ends_with":
                    field_clauses.append(f"{fld} LIKE ?")
                    params.append(f"%{v}")
                else:  # contains
                    field_clauses.append(f"{fld} LIKE ?")
                    params.append(f"%{v}%")
            if field_clauses:
                clauses.append("(" + " OR ".join(field_clauses) + ")")

    if search:
        search_term = search.strip()
        all_fields = get_field_schema()[table]
        search_fields = [
            field
            for field, meta in all_fields.items()
            if meta["type"] in ("text", "textarea", "select", "multi_select")
        ]
        if search_fields:
            validate_fields(table, search_fields)
            subconds = [f"{f} LIKE ?" for f in search_fields]
            clauses.append("(" + " OR ".join(subconds) + ")")
            params.extend([f"%{search_term}%"] * len(subconds))

    return clauses, params

def get_all_records(
    table,
    search=None,
    filters=None,
    ops=None,
    limit=None,
    offset=0,
):
    """Return a list of records honoring search/filter params."""

    validate_table(table)

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            clauses, params = _build_filters(table, search, filters, ops)

            sql = f"SELECT * FROM {table}"
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            if limit is not None:
                sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"

            logger.info(f"[QUERY] SQL: {sql} | params: {params}")
            cursor.execute(sql, params)

            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception as e:
            logger.warning(f"[QUERY ERROR] {e}")
            return []


def count_records(table, search=None, filters=None, ops=None):
    """Return count of records matching the provided filters/search."""

    validate_table(table)
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            clauses, params = _build_filters(table, search, filters, ops)
            sql = f"SELECT COUNT(*) FROM {table}"
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            logger.info(f"[COUNT] SQL: {sql} | params: {params}")
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return row[0] if row else 0
        except Exception as e:
            logger.warning(f"[COUNT ERROR] {e}")
            return 0

def get_record_by_id(table, record_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        fields = [row[1] for row in cursor.fetchall()]
        cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if row:
            return dict(zip(fields, row))
    return None

def update_field_value(table, record_id, field, new_value):
    validate_table(table)
    validate_field(table, field)

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            logger.debug(
                f"update_field_value: table={table}, id={record_id}, field={field}, value={new_value!r}"
            )
            cursor.execute(
                f"UPDATE {table} SET {field} = ? WHERE id = ?",
                (new_value, record_id),
            )
            conn.commit()
            logger.info(
                f"Updated {table}.{field} for id={record_id} to {new_value!r}"
            )
            return True
        except Exception as e:
            logger.error(f"[UPDATE ERROR] {e}")
            return False


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
        except Exception as e:
            logger.warning("[EDIT LOG ERROR] %s", e)


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
        if field.startswith("relation_"):
            from db.relationships import add_relationship, remove_relationship

            rel_table = field[len("relation_") :]
            if old_val is None and new_val is not None:
                add_relationship(table, record_id, rel_table, int(new_val))
            elif new_val is None and old_val is not None:
                remove_relationship(table, record_id, rel_table, int(old_val))
            else:
                return False
        else:
            update_field_value(table, record_id, field, old_val)
        append_edit_log(table, record_id, field, new_val, old_val, actor="undo")
    except Exception:
        logger.exception("Failed to revert edit")
        return False
    return True

def create_record(table, form_data):
    # 1) Validate the table name
    validate_table(table)

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            fields = get_field_schema().get(table, {})
            if not fields:
                return None

            # 2) Figure out real columns on the table
            cursor.execute(f"PRAGMA table_info({table})")
            cols = [col[1] for col in cursor.fetchall()]

            # 3) Build insert_data, but only for known schema fields
            insert_data = {}
            for f, meta in fields.items():
                if f == "id" or meta["type"] == "hidden":
                    continue
                if f not in cols:
                    continue
                validate_field(table, f)
                insert_data[f] = form_data.get(f, "")

            if not insert_data:
                return None

            field_names = list(insert_data.keys())
            placeholders = ", ".join("?" for _ in field_names)
            sql = f"INSERT INTO {table} ({', '.join(field_names)}) VALUES ({placeholders})"
            params = [insert_data[f] for f in field_names]

            cursor.execute(sql, params)
            record_id = cursor.lastrowid
            conn.commit()
            return record_id
        except Exception as e:
            logger.warning(f"[CREATE ERROR] {e}")
            return None

def delete_record(table, record_id):
    validate_table(table)

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
            conn.commit()
            return True
        except Exception as e:
            logger.warning(f"[DELETE ERROR] {e}")
            return False

def count_nonnull(table: str, field: str) -> int:
    validate_table(table)
    logger.info(f"count_nonnull kickoff")
    # Verify that the field exists and is not hidden or "id"
    fmeta = get_field_schema().get(table, {}).get(field)
    if fmeta is None or fmeta.get("type") == "hidden" or field == "id":
        raise ValueError(f"Invalid or protected field: {field}")
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            sql = f'SELECT COUNT(*) FROM "{table}" WHERE "{field}" IS NOT NULL'
            cursor.execute(sql)
            return cursor.fetchone()[0] or 0
        except Exception as e:
            logger.warning(f"[count_nonnull] SQL error for {table}.{field}: {e}")
            return 0


