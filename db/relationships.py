import logging
from db.database import get_connection
from db.validation   import validate_table


def get_related_records(source_table, record_id):
    # 0) Ensure the source table itself is known
    validate_table(source_table)

    conn   = get_connection()
    cursor = conn.cursor()

    # 1) Grab all tables in the SQLite file
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_tables = [row[0] for row in cursor.fetchall()]

    related = {}
    for join_table in all_tables:
        parts = join_table.split("_")
        # only consider the two-way joins
        if len(parts) != 2:
            continue

        table_a, table_b = parts

        # 2) Skip any join tables involving unknown tables
        try:
            validate_table(table_a)
            validate_table(table_b)
        except ValueError:
            continue

        # 3) Is this join relevant to our source?
        if source_table not in (table_a, table_b):
            continue

        # 4) Determine the target side and the join columns
        if source_table == table_a:
            target_table = table_b
            source_field = f"{table_a}_id"
            target_field = f"{table_b}_id"
        else:
            target_table = table_a
            source_field = f"{table_b}_id"
            target_field = f"{table_a}_id"

        # 5) Fetch the related rows safely
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
            logging.warning(f"[RELATED QUERY ERROR on {join_table}] {e}")
            continue

    conn.close()
    return related

def add_relationship(table_a, id_a, table_b, id_b):
    join_table = "_".join(sorted([table_a, table_b]))
    conn = get_connection()
    cursor = conn.cursor()

    # Determine correct column names based on alphabetical sorting
    sorted_tables = sorted([table_a, table_b])
    first_column = f"{sorted_tables[0]}_id"
    second_column = f"{sorted_tables[1]}_id"

    try:
        cursor.execute(
            f"INSERT OR IGNORE INTO {join_table} ({first_column}, {second_column}) VALUES (?, ?)",
            (id_a, id_b)
        )
        conn.commit()
        return True
    except Exception as e:
        logging.warning(f"[RELATIONSHIP ADD ERROR] {e}")
        return False
    finally:
        conn.close()


def remove_relationship(table_a, id_a, table_b, id_b):
    join_table = "_".join(sorted([table_a, table_b]))
    conn = get_connection()
    cursor = conn.cursor()

    sorted_tables = sorted([table_a, table_b])
    first_column = f"{sorted_tables[0]}_id"
    second_column = f"{sorted_tables[1]}_id"

    try:
        cursor.execute(
            f"DELETE FROM {join_table} WHERE {first_column} = ? AND {second_column} = ?",
            (id_a, id_b)
        )
        conn.commit()
        return True
    except Exception as e:
        logging.warning(f"[RELATIONSHIP REMOVE ERROR] {e}")
        return False
    finally:
        conn.close()
