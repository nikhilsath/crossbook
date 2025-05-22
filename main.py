from flask import Flask, render_template, abort, request, redirect, url_for, jsonify, session
import os
import logging
import json
from db.database import get_connection
from db.schema import load_field_schema, update_foreign_field_options, get_field_schema, load_core_tables
from db.records import get_all_records, get_record_by_id, update_field_value, create_record, delete_record
from db.relationships import get_related_records, add_relationship, remove_relationship
from static.imports.validation import validation_sorter
from imports.import_csv import parse_csv
from imports.tasks import huey 
from db.edit_fields import add_column_to_table, add_field_to_schema

app = Flask(__name__, static_url_path='/static')
app.jinja_env.add_extension('jinja2.ext.do') # for field type in detail_view
DB_PATH = os.path.join("data", "crossbook.db")
conn = get_connection()
CORE_TABLES = load_core_tables(conn)

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(message)s"
)
# Before rendering any template call this and inject the results into the template 
@app.context_processor
def inject_field_schema():
    from db.schema import load_field_schema
    from db.schema import update_foreign_field_options
    return {
        'field_schema': load_field_schema(),
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
    # build filters dict
    raw_args = request.args.to_dict()
    filters  = {k: v for k, v in raw_args.items() if k in fields}
    # Operators
    ops = {
        k[:-3]: v
        for k, v in raw_args.items()
        if k.endswith("_op") and k[:-3] in fields
        }
    # Fetch records with both search and filters
    records = get_all_records(table, search=search, filters=filters, ops=ops)
    return render_template(
        "list_view.html",
        table=table,
        fields=fields,
        records=records,
        request=request,
    )

@app.route("/<table>/<int:record_id>")
def detail_view(table, record_id):
    """
    Renders the detail view for a given table and record
    """
    # Fetch the record or 404
    record = get_record_by_id(table, record_id)
    if not record:
        abort(404)

    # Fetch related items
    related = get_related_records(table, record_id)

    # Load full schema (including layout coords) via utility
    FIELD_SCHEMA = load_field_schema()  

    # Extract only the layout mapping for this table
    raw_layout = FIELD_SCHEMA.get(table, {})
    field_schema_layout = {
        field: meta.get("layout", {})
        for field, meta in raw_layout.items()
    }

    logging.debug(f"[DETAIL] Using layout: %s", field_schema_layout)
    # Render template with layout coordinates available as `field_schema_layout`
    return render_template(
        "detail_view.html",
        table=table,
        record=record,
        related=related,
        field_schema_layout=field_schema_layout
    )



@app.route("/<table>/<int:record_id>/add-field", methods=["POST"])
def add_field_route(table, record_id):
    try:
        field_name = request.form["field_name"]
        field_type = request.form["field_type"]
        field_options_raw = request.form.get("field_options", "")
        foreign_key = request.form.get("foreign_key_target", None)

        field_options = [opt.strip() for opt in field_options_raw.split(",") if opt.strip()] if field_options_raw else []
        layout = {"x": 0, "y": 0, "w": 6, "h": 1}

        add_column_to_table(table, field_name, field_type)

        add_field_to_schema(
            table=table,
            field_name=field_name,
            field_type=field_type,
            field_options=field_options,
            foreign_key=foreign_key,
            layout=layout
        )
        from db import schema
        schema.FIELD_SCHEMA = load_field_schema()
        print("🚀 Adding column to:", table, "field:", field_name, "type:", field_type)

        return redirect(url_for("detail_view", table=table, record_id=record_id))

    except Exception as e:
        print("❌ Error:", e)
        return "Server error", 500

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
    FIELD_SCHEMA = load_field_schema()  
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
    conn = get_connection()  # opens a sqlite3 connection
    cur = conn.cursor()
    updated = 0
    for item in layout_items:
        field = item.get("field")
        if not field:
            logging.warning("[LAYOUT] Skipping entry with no field: %r", item)
            continue
        x1 = item.get("x1", 0)
        y1 = item.get("y1", 0)
        x2 = item.get("x2", x1)  # fallback to x1 if missing
        y2 = item.get("y2", y1)  # fallback to y1 if missing
        # Persist coordinates into dedicated columns
        res = cur.execute(
            "UPDATE field_schema SET x1 = ?, y1 = ?, x2 = ?, y2 = ? WHERE table_name = ? AND field_name = ?",
            (x1, y1, x2, y2, table, field)
        )
        if cur.rowcount:
            updated += 1
        else:
            logging.warning("[LAYOUT] No row updated for %s.%s", table, field)
        # Update in-memory schema cache for consistency
        FIELD_SCHEMA[table][field]["layout"] = {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
    conn.commit()
    conn.close()
    logging.info("[LAYOUT] Rows updated: %d", updated)
    return jsonify({"success": True, "updated": updated})

@app.route("/import", methods=["GET", "POST"])
def import_records():
    schema = load_field_schema()
    selected_table = request.args.get("table") or request.form.get("table")
    parsed_headers = []
    rows = []
    num_records = None
    field_status = {}
    validation_results = {}
    file_name = None 

    if request.method == "POST":
        if "file" in request.files:
            file = request.files["file"]
            if file and file.filename.endswith(".csv"):
                parsed_headers, rows = parse_csv(file)
                num_records = len(rows)
                file_name = file.filename

    if selected_table:
        table_schema = schema[selected_table]
        field_status = {
            field: {
                "type": meta["type"],
                "matched": False
            }
            for field, meta in table_schema.items()
            if meta["type"] != "hidden"
        }

    return render_template(
        "import_view.html",
        schema=schema,
        selected_table=selected_table,
        parsed_headers=parsed_headers,
        num_records=num_records,
        field_status=field_status,
        validation_report=validation_results,
        rows=rows,
        file_name=file_name 
    )

@app.route("/trigger-validation", methods=["POST"])
def trigger_validation():
    data = request.get_json(silent=True) or {}
    matched = data.get("matchedFields")
    rows    = data.get("rows")

    if not isinstance(matched, dict) or not isinstance(rows, list):
        return jsonify({"error": "Missing required data"}), 400

    schema = get_field_schema()
    report = {}

    for header, info in matched.items():
        table = info.get("table")
        field = info.get("field")
        if not table or not field:
            continue

        field_type = schema[table][field]["type"]
        values     = [row.get(header, "") for row in rows]
        report[header] = validation_sorter(table, field, header, field_type, values)

    return jsonify(report)

if __name__ == "__main__":
    load_field_schema()
    update_foreign_field_options()
    app.run(debug=True)
