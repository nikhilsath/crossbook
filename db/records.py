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

def create_record(table, form_data):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        fields = get_field_schema().get(table, {})
        if not fields:
            return None

        cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cursor.fetchall()]

        insert_data = {f: form_data.get(f, '') for f in fields if f not in ('id', 'edit_log') and fields[f]['type'] != 'hidden'}
        field_names = [f for f in insert_data if f in columns]

        if not field_names:
            return None

        placeholders = ', '.join('?' for _ in field_names)
        sql = f"INSERT INTO {table} ({', '.join(field_names)}) VALUES ({placeholders})"
        cursor.execute(sql, [insert_data[f] for f in field_names])

        record_id = cursor.lastrowid
        conn.commit()
        return record_id
    except Exception as e:
        import logging
        logging.warning(f"[CREATE ERROR] {e}")
        return None
    finally:
        conn.close()

def delete_record(table, record_id):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
        conn.commit()
        return True
    except Exception as e:
        import logging
        logging.warning(f"[DELETE ERROR] {e}")
        return False
    finally:
        conn.close()