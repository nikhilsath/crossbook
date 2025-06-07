import logging

logger = logging.getLogger(__name__)
from db.database import get_connection
from db.validation import validate_table


def get_related_records(source_table, record_id):
    # Ensure the source table is valid
    validate_table(source_table)
    conn = get_connection()
    cursor = conn.cursor()
    # Fetch all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]
    related = {}
    for join_table in all_tables:
        parts = join_table.split("_")
        if len(parts) != 2:
            continue
        table_a, table_b = parts
        # Validate each side of the join
        try:
            validate_table(table_a)
            validate_table(table_b)
        except ValueError:
            continue

        # Check if this join involves our source table
        if source_table not in (table_a, table_b):
            continue

        # Determine target table and join columns
        if source_table == table_a:
            target_table = table_b
            source_field = f"{table_a}_id"
            target_field = f"{table_b}_id"
        else:
            target_table = table_a
            source_field = f"{table_b}_id"
            target_field = f"{table_a}_id"

        try:
            sql = (
                f"SELECT t.id, t.{target_table} "
                f"FROM {join_table} AS jt "
                f"JOIN {target_table} AS t "
                f"  ON jt.{target_field} = t.id "
                f"WHERE jt.{source_field} = ?"
            )
            cursor.execute(sql, (record_id,))
            rows = cursor.fetchall()

            related[target_table] = {
                "label": target_table.capitalize() + "s",
                "items": [{"id": r[0], "name": r[1]} for r in rows]
            }
        except Exception as e:
            logger.warning(f"[RELATED QUERY ERROR on {join_table}] {e}")
            continue

    conn.close()
    return related


def add_relationship(table_a, id_a, table_b, id_b):
    # Validate entity tables
    validate_table(table_a)
    validate_table(table_b)

    # Construct join table and column names
    sorted_tables = sorted([table_a, table_b])
    join_table = f"{sorted_tables[0]}_{sorted_tables[1]}"
    first_column = f"{sorted_tables[0]}_id"
    second_column = f"{sorted_tables[1]}_id"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Ensure the join table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (join_table,)
        )
        if not cursor.fetchone():
            logger.warning(f"[RELATIONSHIP ADD ERROR] join table {join_table} not found")
            return False

        # Order IDs to match sorted table order
        vals = (id_a, id_b) if table_a == sorted_tables[0] else (id_b, id_a)

        cursor.execute(
            f"INSERT OR IGNORE INTO {join_table} ({first_column}, {second_column}) VALUES (?, ?)",
            vals
        )
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"[RELATIONSHIP ADD ERROR] {e}")
        return False
    finally:
        conn.close()


def remove_relationship(table_a, id_a, table_b, id_b):
    # Validate entity tables
    validate_table(table_a)
    validate_table(table_b)

    # Construct join table and column names
    sorted_tables = sorted([table_a, table_b])
    join_table = f"{sorted_tables[0]}_{sorted_tables[1]}"
    first_column = f"{sorted_tables[0]}_id"
    second_column = f"{sorted_tables[1]}_id"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Ensure the join table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (join_table,)
        )
        if not cursor.fetchone():
            logger.warning(f"[RELATIONSHIP REMOVE ERROR] join table {join_table} not found")
            return False

        # Order IDs to match sorted table order
        vals = (id_a, id_b) if table_a == sorted_tables[0] else (id_b, id_a)

        cursor.execute(
            f"DELETE FROM {join_table} WHERE {first_column} = ? AND {second_column} = ?",
            vals
        )
        conn.commit()
        return True
    except Exception as e:
        logger.warning(f"[RELATIONSHIP REMOVE ERROR] {e}")
        return False
    finally:
        conn.close()
