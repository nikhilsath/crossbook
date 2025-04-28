import logging
from db.database import get_connection
from db.schema import get_field_schema

def get_all_records(table, search=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if search:
            search = search.strip()
            search_fields = [
                field for field, ftype in get_field_schema().get(table, {}).items()
                if ftype["type"] in ("text", "textarea", "select", "single select", "multi select")
            ]
            if not search_fields:
                return []

            conditions = [f"{field} LIKE ?" for field in search_fields]
            sql = f"SELECT * FROM {table} WHERE " + " OR ".join(conditions) + " LIMIT 1000"
            params = [f"%{search}%"] * len(search_fields)
            logging.info(f"[QUERY] SQL: {sql}")
            cursor.execute(sql, params)
        else:
            sql = f"SELECT * FROM {table} LIMIT 1000"
            logging.info(f"[QUERY] SQL: {sql}")
            cursor.execute(sql)

        rows = cursor.fetchall()
        fields = [desc[0] for desc in cursor.description]
        records = [dict(zip(fields, row)) for row in rows]
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
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"UPDATE {table} SET {field} = ? WHERE id = ?", (new_value, record_id))
        conn.commit()
        return True
    except Exception as e:
        logging.warning(f"[UPDATE ERROR] {e}")
        return False
    finally:
        conn.close()
