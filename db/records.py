import logging
from db.database import get_connection
from db.schema import get_field_schema
from db.validation import validate_table, validate_fields, validate_field

def get_all_records(table, search=None, filters=None, ops=None):
    # 1) Validate the table name
    validate_table(table)

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Prepare WHERE clauses and params
        clauses = []
        params = []

        # 2) Apply explicit URL filters (e.g. ?status=Active)
        if filters:
            validate_fields(table, filters.keys())
            for fld, val in filters.items():
                if val == "":
                    continue  # skip empty values
                # Determine operator for field
                op = (ops or {}).get(fld, 'contains')
                if op == 'equals':
                    clauses.append(f"{fld} = ?")
                    params.append(val)
                elif op == 'starts_with':
                    clauses.append(f"{fld} LIKE ?")
                    params.append(f"{val}%")
                elif op == 'ends_with':
                    clauses.append(f"{fld} LIKE ?")
                    params.append(f"%{val}")
                else:  # contains
                    clauses.append(f"{fld} LIKE ?")
                    params.append(f"%{val}%")

        # 3) Apply free-text search across text-like fields
        if search:
            search_term = search.strip()
            all_fields = get_field_schema()[table]
            search_fields = [
                field for field, meta in all_fields.items()
                if meta['type'] in ('text', 'textarea', 'select', 'single select', 'multi select')
            ]
            if search_fields:
                validate_fields(table, search_fields)
                subconds = [f"{f} LIKE ?" for f in search_fields]
                clauses.append("(" + " OR ".join(subconds) + ")")
                params.extend([f"%{search_term}%"] * len(subconds))
            else:
                return []

        # 4) Assemble and execute SQL
        if clauses:
            sql = (
                f"SELECT * FROM {table} "
                + "WHERE " + " AND ".join(clauses)
                + " LIMIT 1000"
            )
            logging.info(f"[QUERY] SQL: {sql} | params: {params}")
            cursor.execute(sql, params)
        else:
            sql = f"SELECT * FROM {table} LIMIT 1000"
            logging.info(f"[QUERY] SQL: {sql}")
            cursor.execute(sql)

        # 5) Hydrate and return results
        rows = cursor.fetchall()
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in rows]

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