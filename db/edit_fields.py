from db.database import get_connection
from db.validation import validate_table, validate_fields, validate_field
from db.schema import get_field_schema

def add_field(table, form_data):
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
