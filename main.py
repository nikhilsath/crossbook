from flask import Flask, render_template, abort, request, redirect, url_for, jsonify, session, g
import os
import logging
import time
import json
from logging_setup import configure_logging
from db.config import get_config_rows, update_config, get_logging_config
from db.database import get_connection
from db.schema import (
    load_field_schema,
    update_foreign_field_options,
    get_field_schema,
    load_base_tables,
    load_card_info,
    update_layout,
    create_base_table,
    refresh_card_cache,
)
from db.records import (
    get_all_records,
    get_record_by_id,
    update_field_value,
    create_record,
    delete_record,
    count_nonnull,
    count_records,
    append_edit_log,
)
from db.relationships import get_related_records, add_relationship, remove_relationship
from static.imports.validation import validation_sorter
from imports.import_csv import parse_csv
from db.edit_fields import add_column_to_table, add_field_to_schema, drop_column_from_table, remove_field_from_schema


app = Flask(__name__, static_url_path='/static')
app.jinja_env.add_extension('jinja2.ext.do') # for field type in detail_view
DB_PATH = os.path.join("data", "crossbook.db")
conn = get_connection()
CARD_INFO = load_card_info(conn)
BASE_TABLES = load_base_tables(conn)
conn.close()

configure_logging(app)


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

@app.context_processor
def inject_field_schema():
    from db.schema import load_field_schema
    from db.schema import update_foreign_field_options
    return {
        'field_schema': load_field_schema(),
        'update_foreign_field_options': update_foreign_field_options,
        'nav_cards': CARD_INFO,
        'base_tables': BASE_TABLES,
    }

@app.route("/")
def home():
    return render_template("index.html", cards=CARD_INFO)


@app.route("/dashboard")
def dashboard():
    """Render the dashboard page."""
    return render_template("dashboard.html")


@app.route("/admin")
def admin_page():
    """Display the admin landing page."""
    return render_template("admin.html")


@app.route("/admin/users")
def admin_users():
    """Placeholder user management page."""
    return render_template("admin_users.html")


@app.route("/admin/automation")
def admin_automation():
    """Placeholder automation page."""
    return render_template("admin_automation.html")


@app.route("/admin.html")
def admin_html_redirect():
    """Redirect legacy /admin.html to the admin page."""
    return redirect(url_for("admin_page"))


@app.route("/admin/config")
def config_page():
    """Display all configuration values grouped by section."""
    configs = get_config_rows()
    sections = {}
    for item in configs:
        sections.setdefault(item["section"], []).append(item)
    return render_template("config_admin.html", sections=sections)


@app.route("/admin/config/<path:key>", methods=["POST"])
def update_config_route(key):
    """Update a configuration key and optionally reload logging."""
    value = request.form.get("value", "")
    update_config(key, value)
    if key in get_logging_config():
        configure_logging(app)
    return redirect(url_for("config_page"))

@app.route("/<table>")
def list_view(table):
    if table not in BASE_TABLES:
        abort(404)
    fields = list(get_field_schema()[table].keys())
    search = request.args.get("search", "").strip()
    raw_args = request.args.to_dict(flat=False)
    filters  = {k: v for k, v in raw_args.items() if k in fields}
    ops = {
        k[:-3]: v
        for k, v in raw_args.items()
        if k.endswith("_op") and k[:-3] in fields
        }
    page = int(request.args.get("page", 1))
    per_page = 500
    offset = (page - 1) * per_page
    records = get_all_records(
        table, search=search, filters=filters, ops=ops, limit=per_page, offset=offset
    )
    total_count = count_records(table, search=search, filters=filters, ops=ops)

    args_without_page = request.args.to_dict(flat=False)
    args_without_page.pop("page", None)
    from urllib.parse import urlencode
    base_qs = urlencode(args_without_page, doseq=True)

    total_pages = (total_count + per_page - 1) // per_page
    start = offset + 1 if total_count else 0
    end = min(offset + len(records), total_count)
    return render_template(
        "list_view.html",
        table=table,
        fields=fields,
        records=records,
        request=request,
        page=page,
        total_pages=total_pages,
        total_count=total_count,
        start=start,
        end=end,
        per_page=per_page,
        base_qs=base_qs,
    )

@app.route("/<table>/<int:record_id>")
def detail_view(table, record_id):
    """
    Renders the detail view for a given table and record
    """
    record = get_record_by_id(table, record_id)
    if not record:
        abort(404)

    related = get_related_records(table, record_id)

    FIELD_SCHEMA = load_field_schema()

    raw_layout = FIELD_SCHEMA.get(table, {})
    field_schema_layout = {
        field: meta.get("layout", {})
        for field, meta in raw_layout.items()
    }

    logging.debug(f"[DETAIL] Using layout: %s", field_schema_layout)
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


@app.route("/<table>/sum-field")
def sum_field_route(table):
    field = request.args.get("field")
    try:
        from db.dashboard import sum_field as _sum_field
        result = _sum_field(table, field)
    except ValueError:
        return jsonify({"sum": 0}), 400

    return jsonify({"sum": result})

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
    field = request.form.get("field")
    if not field:
        abort(400, "Field missing")

    fmeta = get_field_schema().get(table, {}).get(field)
    if not fmeta:
        abort(400, "Unknown field")
    ftype = fmeta["type"]

    if ftype in ("multi_select", "foreign_key"):
        vals      = request.form.getlist("new_value[]")
        new_value = ", ".join(vals)
    else:
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

    prev_record = get_record_by_id(table, record_id)
    prev_value = prev_record.get(field) if prev_record else None

    success = update_field_value(table, record_id, field, new_value)
    if not success:
        abort(500, "Database update failed")

    app.logger.info(
        f"Field updated for {table} id={record_id}: {field} -> {new_value!r}"
    )

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

    CARD_INFO, BASE_TABLES = refresh_card_cache()

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
