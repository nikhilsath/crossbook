from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    request,
    jsonify,
    current_app,
    session,
)
import json
import os
from werkzeug.utils import secure_filename
from logging_setup import configure_logging
from db.config import get_config_rows, update_config
from db.dashboard import (
    get_dashboard_widgets,
    create_widget,
    update_widget_layout,
    update_widget_styling,
    get_base_table_counts,
    get_top_numeric_values,
    get_filtered_records,
)
from db.schema import (
    create_base_table,
    refresh_card_cache,
    update_foreign_field_options,
)
from imports.import_csv import parse_csv
from utils.validation import validation_sorter
from db.schema import get_field_schema
from db.database import get_connection, check_db_status, init_db_path
from db.bootstrap import initialize_database, ensure_default_configs
from imports.tasks import process_import, init_import_table
from utils.field_registry import FIELD_TYPES

admin_bp = Blueprint('admin', __name__)


def reload_app_state() -> None:
    """Refresh cached navigation and schema data after a DB change."""
    card_info, base_tables = refresh_card_cache()
    current_app.config['CARD_INFO'] = card_info
    current_app.config['BASE_TABLES'] = base_tables
    update_foreign_field_options()
    current_app.jinja_env.cache.clear()

@admin_bp.route('/dashboard')
def dashboard():
    widgets = get_dashboard_widgets()
    for w in widgets:
        if w.get('widget_type') == 'table':
            try:
                w['parsed'] = json.loads(w.get('content') or '{}')
            except Exception:
                w['parsed'] = {}
    return render_template('dashboard.html', widgets=widgets)

@admin_bp.route('/admin')
def admin_page():
    return render_template('admin.html')

@admin_bp.route('/admin/users')
def admin_users():
    return render_template('admin_users.html')

@admin_bp.route('/admin/automation')
def admin_automation():
    return render_template('admin_automation.html')

@admin_bp.route('/admin.html')
def admin_html_redirect():
    return redirect(url_for('admin.admin_page'))

@admin_bp.route('/admin/database')
def database_page():
    configs = get_config_rows()
    db_path = None
    db_status = 'missing'
    for item in configs:
        if item['key'] == 'db_path':
            db_path = item['value']
            db_status = check_db_status(db_path)
            break
    return render_template('database_admin.html', db_path=db_path, db_status=db_status)

@admin_bp.route('/admin/config')
def config_page():
    configs = get_config_rows()
    sections = {}
    for item in configs:
        if item.get('type') == 'json':
            try:
                item['parsed'] = json.loads(item.get('value') or '{}')
            except Exception:
                item['parsed'] = {}
        if item['key'] == 'db_path':
            continue
        sections.setdefault(item['section'], []).append(item)
    return render_template('config_admin.html', sections=sections)

@admin_bp.route('/admin/config/<path:key>', methods=['POST'])
def update_config_route(key):
    value = request.form.get('value', '')
    update_config(key, value)
    if key == 'db_path':
        reload_app_state()
    logging_keys = [row['key'] for row in get_config_rows('logging')]
    if key in logging_keys:
        configure_logging(current_app)
    return redirect(url_for('admin.config_page'))


@admin_bp.route('/admin/config/db', methods=['POST'])
def update_database_file():
    """Handle uploaded or newly created database files."""
    wants_json = 'application/json' in request.headers.get('Accept', '')
    if 'file' in request.files and request.files['file'].filename:
        file = request.files['file']
        filename = secure_filename(file.filename)
        if not filename.endswith('.db'):
            return redirect(url_for('admin.database_page'))
        save_path = os.path.join('data', filename)
        file.save(save_path)
        initialize_database(save_path)
        ensure_default_configs(save_path)
        init_db_path(save_path)
        update_config('db_path', save_path)
        reload_app_state()
        if wants_json:
            return jsonify({'db_path': save_path, 'status': check_db_status(save_path)})
        return redirect(url_for('admin.database_page'))

    name = request.form.get('create_name')
    if name:
        filename = secure_filename(name)
        if not filename.endswith('.db'):
            filename += '.db'
        save_path = os.path.join('data', filename)
        open(save_path, 'a').close()
        initialize_database(save_path)
        ensure_default_configs(save_path)
        init_db_path(save_path)
        update_config('db_path', save_path)
        reload_app_state()
        session['wizard_progress'] = {'database': True, 'skip_import': True}
        session.pop('wizard_complete', None)
        if wants_json:
            return jsonify({
                'db_path': save_path,
                'status': check_db_status(save_path),
                'redirect': url_for('wizard.wizard_start'),
            })
        return redirect(url_for('wizard.wizard_start'))
    if wants_json:
        return jsonify({'error': 'no_file'})
    return redirect(url_for('admin.database_page'))

@admin_bp.route('/dashboard/widget', methods=['POST'])
def dashboard_create_widget():
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    widget_type = (data.get('widget_type') or '').strip()
    try:
        col_start = int(data.get('col_start', 1))
        col_span = int(data.get('col_span', 1))
        row_span = int(data.get('row_span', 1))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid layout values'}), 400

    if not title or not widget_type:
        return jsonify({'error': 'Missing required fields'}), 400

    if widget_type not in {'value', 'table', 'chart'}:
        return jsonify({'error': 'Invalid widget type'}), 400

    content = data.get('content')
    if widget_type == 'chart':
        if content is None:
            content = {
                'chart_type': data.get('chart_type', 'bar'),
                'x_field': data.get('x_field'),
                'y_field': data.get('y_field'),
                'aggregation': data.get('aggregation', '')
            }
        if isinstance(content, str):
            try:
                json.loads(content)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON for content'}), 400
        else:
            content = json.dumps(content)
    else:
        if isinstance(content, (dict, list)):
            content = json.dumps(content)
        if content is None:
            content = ''

    widget_id = create_widget(
        title,
        content,
        widget_type,
        col_start,
        col_span,
        None,
        row_span,
    )

    if not widget_id:
        return jsonify({'error': 'Failed to create widget'}), 500

    return jsonify({'success': True, 'id': widget_id})


@admin_bp.route('/dashboard/layout', methods=['POST'])
def dashboard_update_layout():
    data = request.get_json(silent=True)
    if not data or not isinstance(data.get('layout'), list):
        return jsonify({'error': 'Invalid JSON or missing `layout`'}), 400
    layout_items = data['layout']
    updated = update_widget_layout(layout_items)
    return jsonify({'success': True, 'updated': updated})


@admin_bp.route('/dashboard/style', methods=['POST'])
def dashboard_update_style():
    data = request.get_json(silent=True) or {}
    widget_id = data.get('widget_id')
    styling = data.get('styling')
    if widget_id is None or not isinstance(styling, dict):
        return jsonify({'error': 'Invalid data'}), 400
    success = update_widget_styling(widget_id, styling)
    return jsonify({'success': bool(success)})


@admin_bp.route('/dashboard/base-count')
def dashboard_base_count():
    """Return counts for all base tables."""
    data = get_base_table_counts()
    return jsonify(data)


@admin_bp.route('/dashboard/top-numeric')
def dashboard_top_numeric():
    """Return top or bottom numeric values from a table."""
    table = request.args.get('table')
    field = request.args.get('field')
    try:
        limit = int(request.args.get('limit', 10))
    except (TypeError, ValueError):
        limit = 10
    direction = request.args.get('direction', 'desc')
    try:
        data = get_top_numeric_values(
            table,
            field,
            limit=limit,
            ascending=(direction == 'asc'),
        )
    except ValueError:
        return jsonify([]), 400
    return jsonify(data)


@admin_bp.route('/dashboard/filtered-records')
def dashboard_filtered_records():
    """Return filtered records from a table."""
    table = request.args.get('table')
    search = request.args.get('search')
    order_by = request.args.get('order_by')
    try:
        limit = int(request.args.get('limit', 10))
    except (TypeError, ValueError):
        limit = 10
    try:
        data = get_filtered_records(table, filters=search, order_by=order_by, limit=limit)
    except ValueError:
        return jsonify([]), 400
    return jsonify(data)


@admin_bp.route('/api/field-types')
def api_field_types():
    """Return list of available field types."""
    return jsonify(list(FIELD_TYPES.keys()))

@admin_bp.route('/add-table', methods=['POST'])
def add_table():
    data = request.get_json(silent=True) or {}
    table_name = (data.get('table_name') or '').strip()
    description = (data.get('description') or '').strip()

    base_tables = current_app.config['BASE_TABLES']
    if not table_name:
        return jsonify({'error': 'table_name is required'}), 400
    if table_name in base_tables:
        return jsonify({'error': 'Table already exists'}), 400
    if not table_name.isidentifier():
        return jsonify({'error': 'Invalid table name'}), 400
    try:
        success = create_base_table(table_name, description, table_name)
    except Exception as exc:
        current_app.logger.exception('Failed to create table %s: %s', table_name, exc)
        return jsonify({'error': str(exc)}), 400
    if not success:
        return jsonify({'error': 'Failed to create table'}), 400

    reload_app_state()

    return jsonify({'success': True})

@admin_bp.route('/import', methods=['GET', 'POST'])
def import_records():
    schema = get_field_schema()
    selected_table = request.args.get('table') or request.form.get('table')
    parsed_headers = []
    rows = []
    num_records = None
    field_status = {}
    validation_results = {}
    file_name = None

    if request.method == 'POST':
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename.endswith('.csv'):
                parsed_headers, rows = parse_csv(file)
                num_records = len(rows)
                file_name = file.filename

    if selected_table:
        table_schema = schema[selected_table]
        field_status = {
            field: {
                'type': meta['type'],
                'matched': False
            }
            for field, meta in table_schema.items()
            if meta['type'] != 'hidden'
        }

    return render_template(
        'import_view.html',
        schema=schema,
        selected_table=selected_table,
        parsed_headers=parsed_headers,
        num_records=num_records,
        field_status=field_status,
        validation_report=validation_results,
        rows=rows,
        file_name=file_name
    )

@admin_bp.route('/trigger-validation', methods=['POST'])
def trigger_validation():
    data = request.get_json(silent=True) or {}
    matched = data.get('matchedFields')
    rows = data.get('rows')
    if not isinstance(matched, dict) or not isinstance(rows, list):
        return jsonify({'error': 'Missing required data'}), 400

    schema = get_field_schema()
    report = {}

    for header, info in matched.items():
        table = info.get('table')
        field = info.get('field')
        if not table or not field:
            continue
        field_type = schema[table][field]['type']
        values = [row.get(header, '') for row in rows]
        report[header] = validation_sorter(table, field, header, field_type, values)

    return jsonify(report)


@admin_bp.route('/import-start', methods=['POST'])
def import_start_route():
    """Start a background import job and return its ID."""
    if request.is_json:
        data = request.get_json(silent=True) or {}
        table = data.get('table')
        rows = data.get('rows') or []
    else:
        table = request.form.get('table')
        rows = []
        file = request.files.get('file')
        if file and file.filename.endswith('.csv'):
            _, rows = parse_csv(file)

    if not table or not isinstance(rows, list) or not rows:
        return jsonify({'error': 'Invalid import data'}), 400

    init_import_table()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO import_status (status, total_rows, imported_rows, errors) VALUES (?, ?, ?, ?)',
            ('queued', len(rows), 0, '[]')
        )
        import_id = cur.lastrowid
        conn.commit()

    process_import(import_id, table, rows)
    return jsonify({'importId': import_id, 'totalRows': len(rows)})


@admin_bp.route('/import-status')
def import_status_route():
    """Return progress for a given import job."""
    try:
        import_id = int(request.args.get('importId', 0))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid importId'}), 400

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            'SELECT status, total_rows, imported_rows, errors FROM import_status WHERE id = ?',
            (import_id,)
        )
        row = cur.fetchone()

    if not row:
        return jsonify({'error': 'Import not found'}), 404

    status, total_rows, imported_rows, errors_json = row
    errors = json.loads(errors_json or '[]')
    return jsonify({
        'status': status,
        'totalRows': total_rows,
        'importedRows': imported_rows,
        'errorCount': len(errors),
        'errors': errors,
    })
