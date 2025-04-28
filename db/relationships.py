from db.database import get_connection

def get_related_records(source_table, record_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]

    related = {}
    for join_table in all_tables:
        parts = join_table.split("_")
        if len(parts) != 2:
            continue

        table_a, table_b = parts
        if source_table not in (table_a, table_b):
            continue

        if source_table == table_a:
            target_table = table_b
            source_field = f"{table_a}_id"
            target_field = f"{table_b}_id"
        else:
            target_table = table_a
            source_field = f"{table_b}_id"
            target_field = f"{table_a}_id"

        try:
            cursor.execute(f"""
                SELECT t.id, t.{target_table}
                FROM {join_table} jt
                JOIN {target_table} t ON jt.{target_field} = t.id
                WHERE jt.{source_field} = ?
            """, (record_id,))
            rows = cursor.fetchall()
            related[target_table] = {
                "label": target_table.capitalize() + "s",
                "items": [{"id": row[0], "name": row[1]} for row in rows]
            }
        except Exception:
            continue

    conn.close()
    return related