from flask import Flask, render_template, abort, request, redirect, url_for, jsonify
import sqlite3
import os
import datetime
import logging
import json
from schema_utils import load_field_schema, update_foreign_field_options


app = Flask(__name__, static_url_path='/static')
DB_PATH = os.path.join("data", "crossbook.db")
CORE_TABLES = ["character", "thing", "location", "faction", "topic", "content"]
FIELD_SCHEMA = load_field_schema()

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(message)s"
)

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_all_records(table, search=None):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        if search:
            search = search.strip()
            search_fields = [
                field for field, ftype in FIELD_SCHEMA.get(table, {}).items()
                if ftype in ("text", "textarea", "select", "single select", "multi select")
            ]
            if not search_fields:
                return []

            conditions = [f"{field} LIKE ?" for field in search_fields]
            sql = f"SELECT * FROM {table} WHERE " + " OR ".join(conditions) + " LIMIT 1000"
            params = [f"%{search}%"] * len(search_fields)
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


@app.context_processor
def inject_field_schema():
    return {
        'field_schema': FIELD_SCHEMA,
    }

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/<table>")
def list_view(table):
    if table not in CORE_TABLES:
        abort(404)
    fields = list(FIELD_SCHEMA.get(table, {}).keys())
    search = request.args.get("search", "").strip()
    records = get_all_records(table, search=search)
    return render_template(
        "list_view.html", table=table, fields=fields, records=records, request=request,)

@app.route("/<table>/<int:record_id>")
def detail_view(table, record_id):
    conn = get_connection()

    # Get record
    record = get_record_by_id(table, record_id)
    if not record:
        abort(404)

    # Get related records
    related = get_related_records(table, record_id)

    # Load layout info
    cur = conn.execute("SELECT field_name, layout FROM field_schema WHERE table_name = ?", (table,))
    layout_by_field = {}
    for field, layout_json in cur.fetchall():
        try:
            layout_by_field[field] = json.loads(layout_json) if layout_json else {}
        except Exception:
            layout_by_field[field] = {}

    return render_template(
        "detail_view.html",
        table=table,
        record=record,
        related=related,
        field_schema_layout=layout_by_field  
    )


@app.route("/<table>/<int:record_id>/update", methods=["POST"])
def update_field(table, record_id):
    if table not in CORE_TABLES:
        abort(404)

    field = request.form.get("field")
    raw_value = request.form.get("new_value_override") or request.form.get("new_value", "")

    if field in ["id", "edit_log"]:
        abort(403)

    record = get_record_by_id(table, record_id)
    if not record:
        abort(404)

    table_schema = FIELD_SCHEMA.get(table, {})
    entry = table_schema.get(field, {})
    field_type = entry.get("type", "text")


    # Special handling for multi_select FIRST
    if field_type in ("multi_select", "foreign_key"):
        raw_values = request.form.getlist("new_value[]")
        value = ", ".join(raw_values)  # override value
        print(f"[DEBUG] Incoming multi_select update for {table}.{field}: {raw_values} -> {value}")
    else:
        # Coerce value based on field_type
        if field_type == "boolean":
            value = "1" if raw_value in ("on", "1", "true", "True") else "0"
        elif field_type == "number":
            try:
                value = int(raw_value)
            except ValueError:
                value = 0
        else:
            value = raw_value

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        f'UPDATE "{table}" SET "{field}" = ? WHERE id = ?',
        (value, record_id)
    )

    # Append to edit log only if value changed
    old_value = str(record.get(field))
    if str(value) != old_value:
        timestamp = datetime.datetime.now().isoformat(timespec='seconds')
        log_entry = f"[{timestamp}] Updated {field} from '{old_value}' to '{value}'"
        new_log = (record.get("edit_log") or "") + "\n" + log_entry
        cursor.execute(f"UPDATE {table} SET edit_log = ? WHERE id = ?", (new_log.strip(), record_id))

    conn.commit()
    conn.close()
    return redirect(url_for("detail_view", table=table, record_id=record_id))

@app.route('/relationship', methods=['POST'])
def manage_relationship():
    import json
    from flask import request, jsonify

    data = request.get_json()
    required_fields = {'table_a', 'id_a', 'table_b', 'id_b', 'action'}
    if not data or not required_fields.issubset(data):
        return jsonify({"error": "Missing required fields"}), 400

    # Sort table names to match join table convention
    table1, table2 = sorted([data["table_a"], data["table_b"]])
    id1_field = f"{table1}_id"
    id2_field = f"{table2}_id"
    join_table = f"{table1}_{table2}"

    try:
        conn = sqlite3.connect("data/crossbook.db")
        cur = conn.cursor()

        if data["action"] == "add":
            cur.execute(f"""
                INSERT OR IGNORE INTO {join_table} ({id1_field}, {id2_field})
                VALUES (?, ?)
            """, (data["id_a"], data["id_b"]) if data["table_a"] == table1 else (data["id_b"], data["id_a"]))

        elif data["action"] == "remove":
            cur.execute(f"""
                DELETE FROM {join_table}
                WHERE {id1_field} = ? AND {id2_field} = ?
            """, (data["id_a"], data["id_b"]) if data["table_a"] == table1 else (data["id_b"], data["id_a"]))

        else:
            return jsonify({"error": "Invalid action"}), 400

        conn.commit()
        return jsonify({"success": True}), 200

    except sqlite3.OperationalError as e:
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    finally:
        conn.close()

@app.route('/<table>/new', methods=['GET', 'POST'])
def create_record(table):
    if table not in CORE_TABLES:
        abort(404)

    fields = FIELD_SCHEMA.get(table, {})
    if request.method == 'POST':
        data = {f: request.form.get(f, '') for f in fields if f not in ('id', 'edit_log') and fields[f] != 'hidden'}

        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in cur.fetchall()]
        field_names = [f for f in data.keys() if f in columns]
        placeholders = ', '.join('?' for _ in field_names)
        sql = f"INSERT INTO {table} ({', '.join(field_names)}) VALUES ({placeholders})"
        cur.execute(sql, [data[f] for f in field_names])
        record_id = cur.lastrowid
        conn.commit()
        conn.close()

        return redirect(f"/{table}/{record_id}")

    return render_template('new_record.html', table=table, fields=fields)

@app.route('/<table>/<int:record_id>/delete', methods=['POST'])
def delete_record(table, record_id):
    if table not in CORE_TABLES:
        abort(404)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"DELETE FROM {table} WHERE id = ?", (record_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('list_view', table=table))

@app.route("/<table>/layout", methods=["POST"])
def update_layout(table):
    data = request.get_json()
    layout_items = data.get("layout", [])

    if not layout_items or table not in FIELD_SCHEMA:
        return jsonify({"error": "Invalid data"}), 400

    conn = get_connection()
    cur = conn.cursor()

    for item in layout_items:
        field = item.get("field")
        layout_data = {
            "x": item.get("x", 0),
            "y": item.get("y", 0),
            "w": item.get("w", 1),
            "h": item.get("h", 1)
        }

        if not field:
            continue  # Skip broken entries

        cur.execute("""
            UPDATE field_schema
            SET layout = ?
            WHERE table_name = ? AND field_name = ?
        """, (json.dumps(layout_data), table, field))

    conn.commit()
    conn.close()
    return jsonify({"success": True})



if __name__ == "__main__":
    load_field_schema()
    update_foreign_field_options()
    app.run(debug=True)
