import logging
from db.database import get_connection
from db.schema import get_field_schema
from db.validation import validate_table, validate_fields, validate_field

def get_all_records(table, search=None):
    # 1) Validate the table name
    validate_table(table)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        if search:
            search = search.strip()

            # 2) Determine which fields are searchable
            all_fields    = get_field_schema()[table]
            search_fields = [
                field
                for field, meta in all_fields.items()
                if meta["type"] in ("text", "textarea", "select", "multi select")
            ]

            if not search_fields:
                return []

            # 3) Validate each field name
            validate_fields(table, search_fields)

            # 4) Build the safe SQL string with placeholders
            conditions = [f"{fld} LIKE ?" for fld in search_fields]
            sql        = (
                f"SELECT * FROM {table} "
                + "WHERE " + " OR ".join(conditions)
                + " LIMIT 1000"
            )
            params     = [f"%{search}%"] * len(search_fields)

            cursor.execute(sql, params)
        else:
            # No search term: just return the first 1,000 rows
            cursor.execute(f"SELECT * FROM {table} LIMIT 1000")

        # 5) Hydrate the results
        rows    = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        records = [dict(zip(columns, row)) for row in rows]

        return records

    except Exception as e:
        logging.warning(f"[QUERY ERROR] {e}")
        return []
    finally:
        conn.close()

def get_record_by_id(table, record_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    fields = [row[1] for row in cursor.fetchall()]
    cursor.execute(f"SELECT * FROM {table} WHERE id = ?", (record_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(zip(fields, row))
    return None

def update_field_value(table, record_id, field, new_value):
    validate_table(table)
    validate_field(table, field)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            f"UPDATE {table} SET {field} = ? WHERE id = ?",  # identifiers are validated
            (new_value, record_id)
        )
        conn.commit()
        return True
    except Exception as e:
        logging.warning(f"[UPDATE ERROR] {e}")
        return False
    finally:
        conn.close()

def create_record(table, form_data):
    # 1) Validate the table name
    validate_table(table)

    conn   = get_connection()
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
            if f in ("id", "edit_log") or meta["type"] == "hidden":
                continue
            # validate each column before we use it
            if f not in cols:
                continue
            validate_field(table, f)
            insert_data[f] = form_data.get(f, "")

        if not insert_data:
            return None

        field_names = list(insert_data.keys())
        placeholders = ", ".join("?" for _ in field_names)
        sql          = f"INSERT INTO {table} ({', '.join(field_names)}) VALUES ({placeholders})"
        params       = [insert_data[f] for f in field_names]

        cursor.execute(sql, params)
        record_id = cursor.lastrowid
        conn.commit()
        return record_id

    except Exception as e:
        logging.warning(f"[CREATE ERROR] {e}")
        return None

    finally:
        conn.close()

def delete_record(table, record_id):
    validate_table(table)

    conn   = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
        conn.commit()
        return True
    except Exception as e:
        logging.warning(f"[DELETE ERROR] {e}")
        return False
    finally:
        conn.close()