import logging
import sqlite3

logger = logging.getLogger(__name__)
import datetime
from db.database import get_connection
from db.schema import get_field_schema
from db.validation import validate_table, validate_field
from db.query_filters import _build_filters



def get_all_records(
    table,
    search=None,
    filters=None,
    ops=None,
    modes=None,
    sort_field=None,
    direction="asc",
    limit=None,
    offset=0,
):
    """Return a list of records honoring search/filter params."""

    validate_table(table)

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            clauses, params = _build_filters(table, search, filters, ops, modes)

            sql = f"SELECT * FROM {table}"
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)

            if sort_field:
                try:
                    validate_field(table, sort_field)
                    dir_sql = "DESC" if str(direction).lower() == "desc" else "ASC"
                    sql += f" ORDER BY {sort_field} COLLATE NOCASE {dir_sql}"
                except ValueError:
                    logger.exception(
                        "Invalid sort field: %s",
                        sort_field,
                        extra={"table": table, "sort_field": sort_field},
                    )

            if limit is not None:
                sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"

            logger.info(
                "[QUERY] SQL: %s | params: %s",
                sql,
                params,
                extra={"table": table},
            )
            cursor.execute(sql, params)

            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            return [dict(zip(cols, row)) for row in rows]
        except (sqlite3.DatabaseError, ValueError) as e:
            logger.exception(
                "[QUERY ERROR] %s",
                e,
                extra={"table": table, "error": str(e)},
            )
            return []


def count_records(table, search=None, filters=None, ops=None, modes=None):
    """Return count of records matching the provided filters/search."""

    validate_table(table)
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            clauses, params = _build_filters(table, search, filters, ops, modes)
            sql = f"SELECT COUNT(*) FROM {table}"
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            logger.info(
                "[COUNT] SQL: %s | params: %s",
                sql,
                params,
                extra={"table": table},
            )
            cursor.execute(sql, params)
            row = cursor.fetchone()
            return row[0] if row else 0
        except (sqlite3.DatabaseError, ValueError) as e:
            logger.exception(
                "[COUNT ERROR] %s",
                e,
                extra={"table": table, "error": str(e)},
            )
            return 0

def get_record_by_id(table, record_id):
    validate_table(table)
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table})")
        fields = [row[1] for row in cursor.fetchall()]
        cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        if row:
            record = dict(zip(fields, row))

            # Sanitize any textarea fields on retrieval to guard against
            # potentially unsafe HTML that may have been stored before
            # sanitization was implemented.
            schema = get_field_schema().get(table, {})
            from utils.html_sanitizer import sanitize_html
            for field_name, meta in schema.items():
                if meta.get("type") == "textarea" and field_name in record:
                    record[field_name] = sanitize_html(record[field_name] or "")

            return record
    return None


def touch_last_edited(table: str, record_id: int) -> None:
    """Update the last_edited timestamp for a record if the column exists."""
    validate_table(table)

    timestamp = datetime.datetime.utcnow().isoformat(timespec="seconds")

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        cols = [row[1] for row in cur.fetchall()]
        if "last_edited" not in cols:
            return
        cur.execute(
            f"UPDATE {table} SET last_edited = ? WHERE id = ?",
            (timestamp, record_id),
        )
        conn.commit()

def update_field_value(table, record_id, field, new_value):
    validate_table(table)
    validate_field(table, field)

    # Sanitize textarea HTML before saving
    fmeta = get_field_schema().get(table, {}).get(field, {})
    if fmeta.get("type") == "textarea":
        from utils.html_sanitizer import sanitize_html
        new_value = sanitize_html(new_value)

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            logger.debug(
                "update_field_value: table=%s id=%s field=%s value=%r",
                table,
                record_id,
                field,
                new_value,
                extra={
                    "table": table,
                    "record_id": record_id,
                    "field": field,
                },
            )
            cursor.execute(
                f"UPDATE {table} SET {field} = ? WHERE id = ?",
                (new_value, record_id),
            )
            conn.commit()
            logger.info(
                "Updated %s.%s for id=%s to %r",
                table,
                field,
                record_id,
                new_value,
                extra={
                    "table": table,
                    "field": field,
                    "record_id": record_id,
                },
            )
            success = True
        except sqlite3.DatabaseError as e:
            logger.exception(
                "[UPDATE ERROR] %s",
                e,
                extra={
                    "table": table,
                    "record_id": record_id,
                    "field": field,
                    "error": str(e),
                },
            )
            success = False
        if success:
            touch_last_edited(table, record_id)
        return success


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
            from utils.html_sanitizer import sanitize_html

            for f, meta in fields.items():
                if f == "id" or meta["type"] == "hidden":
                    continue
                if f not in cols:
                    continue
                validate_field(table, f)
                value = form_data.get(f, "")
                if meta["type"] == "textarea":
                    value = sanitize_html(value)
                insert_data[f] = value

            timestamp = datetime.datetime.utcnow().isoformat(timespec="seconds")
            if "date_created" in cols:
                insert_data.setdefault("date_created", timestamp)
            if "last_edited" in cols:
                insert_data.setdefault("last_edited", timestamp)

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
        except (sqlite3.DatabaseError, ValueError) as e:
            logger.exception(
                "[CREATE ERROR] %s",
                e,
                extra={"table": table, "error": str(e)},
            )
            return None

def delete_record(table, record_id):
    validate_table(table)

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
            conn.commit()
            return True
        except sqlite3.DatabaseError as e:
            logger.exception(
                "[DELETE ERROR] %s",
                e,
                extra={"table": table, "record_id": record_id, "error": str(e)},
            )
            return False

def count_nonnull(table: str, field: str) -> int:
    validate_table(table)
    logger.info(
        "count_nonnull kickoff",
        extra={"table": table, "field": field},
    )
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
        except sqlite3.DatabaseError as e:
            logger.exception(
                "[count_nonnull] SQL error for %s.%s: %s",
                table,
                field,
                e,
                extra={"table": table, "field": field, "error": str(e)},
            )
            return 0


def field_distribution(table: str, field: str) -> dict[str, int]:
    """Return counts of each distinct value for a field."""
    validate_table(table)
    validate_field(table, field)
    fmeta = get_field_schema().get(table, {}).get(field)
    if fmeta is None or fmeta.get("type") == "hidden" or field == "id":
        raise ValueError(f"Invalid field: {field}")

    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                f'SELECT "{field}" FROM "{table}" WHERE "{field}" IS NOT NULL'
            )
            rows = [r[0] for r in cursor.fetchall()]
        except sqlite3.DatabaseError as e:
            logger.exception(
                "[field_distribution] SQL error for %s.%s: %s",
                table,
                field,
                e,
                extra={"table": table, "field": field, "error": str(e)},
            )
            return {}

    counts: dict[str, int] = {}
    for val in rows:
        if val is None or val == "":
            continue
        if fmeta["type"] == "multi_select":
            parts = [p.strip() for p in str(val).split(',') if p.strip()]
            for p in parts:
                counts[p] = counts.get(p, 0) + 1
        else:
            counts[str(val)] = counts.get(str(val), 0) + 1
    return counts


