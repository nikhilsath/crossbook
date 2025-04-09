# This function dynamically joins a source table to a target table using a join table.
# It assumes the join table uses the convention: {target_label}_id (e.g., thing_id, topic_id).
# For compound target labels (e.g., "topic"), the join table column must still follow the format: topic_id.

def fetch_related(cursor, join_table, source_field, target_table, target_label, source_id):
    cursor.execute(f"""
        SELECT t.id, t.{target_label}
        FROM {join_table} j
        JOIN {target_table} t ON j.{target_label}_id = t.id
        WHERE j.{source_field} = ?
    """, (source_id,))
    return cursor.fetchall()
