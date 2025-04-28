from flask import Flask, render_template, abort, request, redirect, url_for, jsonify
import sqlite3
import os
import datetime
import logging
import json
from db.database import get_connection
from db.schema import load_field_schema, update_foreign_field_options, get_field_schema
from db.records import get_all_records, get_record_by_id, update_field_value, create_record, delete_record
from db.relationships import get_related_records, add_relationship, remove_relationship

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


@app.route("/<table>/<int:record_id>/update", methods=["POST"])
def update_field(table, record_id):
    # grab which column we’re editing
    field = request.form.get("field")
    if not field:
        abort(400, "Field missing")

    # figure out the declared type
    fmeta = get_field_schema().get(table, {}).get(field)
    if not fmeta:
        abort(400, "Unknown field")
    ftype = fmeta["type"]

    # --- HANDLE MULTI-SELECT & FOREIGN-KEY AS A LIST ---
    if ftype in ("multi_select", "foreign_key"):
        # checkboxes all name="new_value[]"
        vals      = request.form.getlist("new_value[]")
        new_value = ", ".join(vals)
    else:
        # everything else uses a single input or override
        raw = request.form.get("new_value_override") or request.form.get("new_value", "")
        if ftype == "boolean":
            new_value = "1" if raw.lower() in ("1","on","true") else "0"
        elif ftype == "number":
            try:
                new_value = int(raw)
            except ValueError:
                new_value = 0
        else:
            new_value = raw

    # Delegate to your existing DB helper
    success = update_field_value(table, record_id, field, new_value)
    if not success:
        abort(500, "Database update failed")
    return redirect(url_for("detail_view", table=table, record_id=record_id))

@app.route('/relationship', methods=['POST'])
def manage_relationship():
    data = request.get_json()

    action = data.get('action')
    table_a = data.get('table_a')
    id_a = data.get('id_a')
    table_b = data.get('table_b')
    id_b = data.get('id_b')

    if action == 'add':
        success = add_relationship(table_a, id_a, table_b, id_b)
    elif action == 'remove':
        success = remove_relationship(table_a, id_a, table_b, id_b)
    else:
        abort(400, "Invalid action")

    if not success:
        abort(500, "Failed to modify relationship")

    return {"success": True}


@app.route('/<table>/new', methods=['GET', 'POST'])
def create_record_route(table):
    if table not in CORE_TABLES:
        abort(404)

    fields = get_field_schema().get(table, {})

    if request.method == 'POST':
        record_id = create_record(table, request.form)
        if record_id:
            return redirect(f"/{table}/{record_id}")
        else:
            abort(500, "Failed to create record")

    return render_template('new_record.html', table=table, fields=fields)


@app.route('/<table>/<int:record_id>/delete', methods=['POST'])
def delete_record_route(table, record_id):
    if table not in CORE_TABLES:
        abort(404)
    success = delete_record(table, record_id)
    if not success:
        abort(500, "Failed to delete record")
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
