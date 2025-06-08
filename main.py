from flask import Flask, render_template, abort, request, redirect, url_for, jsonify, session, g
import os
import sqlite3
import logging
import time
import json
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from db.database import get_connection
from db.schema import (
    load_field_schema,
    update_foreign_field_options,
    get_field_schema,
    load_base_tables,
    load_card_info,
    update_layout,
    create_base_table,
)
from db.records import (
    get_all_records,
    get_record_by_id,
    update_field_value,
    create_record,
    delete_record,
    count_nonnull,
    append_edit_log,
)
from db.relationships import get_related_records, add_relationship, remove_relationship
from static.imports.validation import validation_sorter
from imports.import_csv import parse_csv
from db.edit_fields import add_column_to_table, add_field_to_schema, drop_column_from_table, remove_field_from_schema
from db.config import get_logging_config, get_config_value


app = Flask(__name__, static_url_path='/static')
app.jinja_env.add_extension('jinja2.ext.do') # for field type in detail_view
DB_PATH = os.path.join("data", "crossbook.db")
conn = get_connection()
CARD_INFO = load_card_info(conn)
BASE_TABLES = load_base_tables(conn)
cfg = get_logging_config()
app.logger.handlers.clear()
level_name = cfg.get("log_level", "INFO").upper()
level = getattr(logging, level_name, logging.INFO)
handler_type = cfg.get("handler_type", "stream")
filename = cfg.get("filename", "logs/crossbook.log")
max_bytes = int(cfg.get("max_file_size", 5 * 1024 * 1024))
backup = int(cfg.get("backup_count", 3))
when_interval = cfg.get("when_interval", "midnight")
interval = int(cfg.get("interval_count", 1))
log_fmt = cfg.get(
    "log_format",
    "[%(asctime)s] %(levelname)s in %(module)s:%(funcName)s: %(message)s",
)

if handler_type == "rotating":
    import os
    log_dir = os.path.dirname(filename)
    if log_dir and not os.path.isdir(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    file_handler = RotatingFileHandler(
        filename,
        maxBytes=max_bytes,
        backupCount=backup
    )
elif handler_type == "timed":
    file_handler = TimedRotatingFileHandler(
        filename,
        when=when_interval,
        interval=interval,
        backupCount=backup
    )
else:  # default to 'stream'
    file_handler = logging.StreamHandler()

formatter = logging.Formatter(log_fmt)
file_handler.setFormatter(formatter)
file_handler.setLevel(level)

console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
console_handler.setLevel(logging.WARNING)

app.logger.setLevel(level)
app.logger.addHandler(file_handler)
root_logger = logging.getLogger()
root_logger.setLevel(level)
root_logger.addHandler(file_handler)
app.logger.addHandler(console_handler)
app.logger.propagate = False


# Disable Werkzeug's default request logging
werk_logger = logging.getLogger("werkzeug")
werk_logger.disabled = True



@app.before_request
def start_timer():
    g.start_time = time.time()
    app.logger.info(f"[REQ] {request.method} {request.path} started")

@app.after_request
def log_request(response):
    duration = time.time() - g.get("start_time", time.time())
    app.logger.info(f"[REQ] {request.method} {request.path} completed in {duration:.3f}s with {response.status_code}")
    return response

@app.teardown_request
def log_exception(exc):
    if exc:
        app.logger.exception(f"[ERROR] Unhandled exception during {request.method} {request.path}: {exc}")

# Before rendering any template call this and inject the results into the template 
@app.context_processor
def inject_field_schema():
    from db.schema import load_field_schema
    from db.schema import update_foreign_field_options
    return {
        'field_schema': load_field_schema(),
        'update_foreign_field_options': update_foreign_field_options,
        'nav_cards': CARD_INFO,
    }

@app.route("/")
def home():
    heading = get_config_value("index.heading", "Load the Glass Cannon")
    return render_template("index.html", cards=CARD_INFO, heading=heading)


@app.route("/dashboard")
def dashboard():
    """Render the dashboard page."""
    return render_template("dashboard.html")

@app.route("/<table>")
def list_view(table):
    if table not in BASE_TABLES:
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
        app.logger.debug(
            f"add_field_route start: table={table!r}, record_id={record_id!r}, form={dict(request.form)!r}"
        )
        app.logger.info(
            "table=%s record_id=%s form=%s",
            table,
            record_id,
            dict(request.form),
        )
        field_type = request.form["field_type"]
        field_options_raw = request.form.get("field_options", "")
        foreign_key = request.form.get("foreign_key_target", None)

        field_options = [opt.strip() for opt in field_options_raw.split(",") if opt.strip()] if field_options_raw else []
        layout = {"x": 0, "y": 0, "w": 6, "h": 1}

        app.logger.debug(
            "add_field_route calling add_column_to_table table=%r field_name=%r field_type=%r",
            table,
            field_name,
            field_type,
        )
        app.logger.info(
            "Calling add_column_to_table table=%s field_name=%s field_type=%s",
            table,
            field_name,
            field_type,
        )
        add_column_to_table(table, field_name, field_type)
        app.logger.info("Returned from add_column_to_table for field %s", field_name)
        app.logger.debug(
            "add_field_route calling add_field_to_schema table=%r field_name=%r field_type=%r options=%r fk=%r",
            table,
            field_name,
            field_type,
            field_options,
            foreign_key,
        )
        app.logger.info(
            "Calling add_field_to_schema table=%s field_name=%s field_type=%s options=%s fk=%s",
            table,
            field_name,
            field_type,
            field_options,
            foreign_key,
        )

        add_field_to_schema(
            table=table,
            field_name=field_name,
            field_type=field_type,
            field_options=field_options,
            foreign_key=foreign_key
        )
        from db import schema
        schema.FIELD_SCHEMA = load_field_schema()
        app.logger.info(
            f"Added column to {table}: field={field_name!r} type={field_type!r}"
            "🚀 Added column: table=%s field=%s type=%s",
            table,
            field_name,
            field_type,
        )

        return redirect(url_for("detail_view", table=table, record_id=record_id))

    except Exception as e:
        app.logger.exception("add_field_route error: %s", e)
        app.logger.exception("Error adding field")
        return "Server error", 500

@app.route("/<table>/count-nonnull")
def count_nonnull(table):
    field = request.args.get("field")
    try:
        from db.records import count_nonnull as _count_nonnull
        count = _count_nonnull(table, field)
    except ValueError:
        return jsonify({"count": 0}), 400

    return jsonify({"count": count})

@app.route("/<table>/<int:record_id>/remove-field", methods=["POST"])
def remove_field_route(table, record_id):
    field_name = request.form.get("field_name")
    # Validate it again
    fmeta = get_field_schema().get(table, {}).get(field_name)
    if not field_name or fmeta is None or fmeta["type"] == "hidden" or field_name == "id":
        abort(400, "Invalid field")
    # 1) Drop column from DB and remove from schema
    from db.edit_fields import drop_column_from_table, remove_field_from_schema
    drop_column_from_table(table, field_name)
    remove_field_from_schema(table, field_name)
    # 2) Reload FIELD_SCHEMA in memory
    from db import schema
    schema.FIELD_SCHEMA = load_field_schema()
    return redirect(url_for("detail_view", table=table, record_id=record_id))

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

    app.logger.debug(
        f"update_field: table={table}, id={record_id}, field={field}, value={new_value!r}"
    )

    # Delegate to your existing DB helper
    # First fetch the previous value so we can record changes
    prev_record = get_record_by_id(table, record_id)
    prev_value = prev_record.get(field) if prev_record else None

    success = update_field_value(table, record_id, field, new_value)
    if not success:
        abort(500, "Database update failed")

    app.logger.info(
        f"Field updated for {table} id={record_id}: {field} -> {new_value!r}"
    )

    # Append to the edit log if the value actually changed
    if prev_record is not None and str(prev_value) != str(new_value):
        append_edit_log(
            table,
            record_id,
            f"Updated {field}: {prev_value!r} -> {new_value!r}",
        )

    return redirect(url_for("detail_view", table=table, record_id=record_id))

@app.route('/relationship', methods=['POST'])
def manage_relationship():
    data = request.get_json()

    app.logger.debug(f"manage_relationship request: {data}")

    action = data.get('action')
    table_a = data.get('table_a')
    id_a = data.get('id_a')
    table_b = data.get('table_b')
    id_b = data.get('id_b')

    if action == 'add':
        success = add_relationship(table_a, id_a, table_b, id_b)
        if success:
            append_edit_log(
                table_a,
                id_a,
                f"Added relation to {table_b} {id_b}",
            )
    elif action == 'remove':
        success = remove_relationship(table_a, id_a, table_b, id_b)
        if success:
            append_edit_log(
                table_a,
                id_a,
                f"Removed relation to {table_b} {id_b}",
            )
    else:
        abort(400, "Invalid action")

    if not success:
        app.logger.error(
            f"manage_relationship failed action={action} {table_a}:{id_a} -> {table_b}:{id_b}"
        )
        abort(500, "Failed to modify relationship")
    else:
        app.logger.info(
            f"manage_relationship {action} {table_a}:{id_a} {table_b}:{id_b}"
        )

    return {"success": True}

@app.route('/<table>/new', methods=['GET', 'POST'])
def create_record_route(table):
    if table not in BASE_TABLES:
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
    if table not in BASE_TABLES:
        abort(404)
    success = delete_record(table, record_id)
    if not success:
        abort(500, "Failed to delete record")
    return redirect(url_for('list_view', table=table))

@app.route("/<table>/layout", methods=["POST"])
def update_layout(table):
    data = request.get_json(silent=True)
    if not data or not isinstance(data.get("layout"), list):
        return jsonify({"error": "Invalid JSON or missing `layout`"}), 400

    layout_items = data["layout"]
    try:
        from db.schema import update_layout as _update_layout
        updated = _update_layout(table, layout_items)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({"success": True, "updated": updated})


@app.route("/add-table", methods=["POST"])
def add_table():
    """Create a new base table using JSON input."""
    global CARD_INFO, BASE_TABLES
    data = request.get_json(silent=True) or {}
    table_name = (data.get("table_name") or "").strip()
    description = (data.get("description") or "").strip()

    if not table_name:
        return jsonify({"error": "table_name is required"}), 400

    if table_name in BASE_TABLES:
        return jsonify({"error": "Table already exists"}), 400

    if not table_name.isidentifier():
        return jsonify({"error": "Invalid table name"}), 400

    try:
        success = create_base_table(table_name, description)
    except Exception as exc:
        app.logger.exception("Failed to create table %s: %s", table_name, exc)
        return jsonify({"error": str(exc)}), 400

    if not success:
        return jsonify({"error": "Failed to create table"}), 400

    with sqlite3.connect(DB_PATH) as c:
        CARD_INFO = load_card_info(c)
        BASE_TABLES = load_base_tables(c)

    return jsonify({"success": True})

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
