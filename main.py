from flask import Flask, render_template, abort, request, redirect, url_for, jsonify
import sqlite3
import os
import datetime
import logging
import json
from db.database import get_connection
from db.schema import load_field_schema, update_foreign_field_options, get_field_schema
from db.records import get_all_records, get_record_by_id, update_field_value
from db.relationships import get_related_records


app = Flask(__name__, static_url_path='/static')
DB_PATH = os.path.join("data", "crossbook.db")
CORE_TABLES = ["character", "thing", "location", "faction", "topic", "content"]

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(message)s"
)



@app.context_processor
def inject_field_schema():
    from db.schema import get_field_schema  
    return {
        'field_schema': get_field_schema(),
        'update_foreign_field_options': update_foreign_field_options
    }


@app.route("/")
def home():
    return render_template("index.html")

@app.route("/<table>")
def list_view(table):
    if table not in CORE_TABLES:
        abort(404)
    fields = list(get_field_schema()[table].keys())
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


@app.route('/<table>/<int:record_id>/update', methods=['POST'])
def update_field(table, record_id):
    field = request.form.get('field')
    new_value = request.form.get('new_value') or request.form.get('new_value_override')

    if not field:
        abort(400, "Field missing")

    # Validate field is allowed to update
    if field not in get_field_schema().get(table, {}):
        abort(400, "Invalid field")

    # Type coercion (optional, depending how strict you want to be)
    field_type = get_field_schema()[table][field]["type"]

    if field_type == "boolean":
        new_value = "1" if new_value in ("1", 1, "true", True) else "0"
    elif field_type == "number":
        try:
            new_value = int(new_value)
        except ValueError:
            new_value = 0
    # Other types (text, select, etc.) left as strings

    success = update_field_value(table, record_id, field, new_value)

    if not success:
        abort(500, "Failed to update field")

    return redirect(url_for('detail_view', table=table, record_id=record_id))


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
    logging.info(f"[LAYOUT] Received payload for table={table}: %s", request.get_data())
    data = request.get_json(silent=True)
    if data is None:
        logging.error("[LAYOUT] JSON parse failed")
        return jsonify({"error": "Bad JSON"}), 400

    layout_items = data.get("layout")
    if not isinstance(layout_items, list):
        logging.error("[LAYOUT] Missing or invalid `layout` field: %r", layout_items)
        return jsonify({"error": "Invalid layout format"}), 400

    if table not in FIELD_SCHEMA:
        logging.error("[LAYOUT] Unknown table: %s", table)
        return jsonify({"error": "Unknown table"}), 400

    conn = get_connection()
    cur = conn.cursor()
    updated = 0

    for item in layout_items:
        field = item.get("field")
        if not field:
            logging.warning("[LAYOUT] Skipping entry with no field: %r", item)
            continue

        layout_data = {
            "x": item.get("x", 0),
            "y": item.get("y", 0),
            "w": item.get("w", 1),
            "h": item.get("h", 1)
        }

        res = cur.execute(
            "UPDATE field_schema SET layout = ? WHERE table_name = ? AND field_name = ?",
            (json.dumps(layout_data), table, field)
        )
        if cur.rowcount:
            updated += 1
        else:
            logging.warning("[LAYOUT] No row updated for %s.%s", table, field)
        FIELD_SCHEMA[table][field]["layout"] = layout_data

    conn.commit()
    conn.close()

    logging.info("[LAYOUT] Rows updated: %d", updated)
    return jsonify({"success": True, "updated": updated})




if __name__ == "__main__":
    load_field_schema()
    update_foreign_field_options()
    app.run(debug=True)
