from flask import Blueprint, render_template, redirect, url_for, request, jsonify, current_app
from logging_setup import configure_logging
from db.config import get_config_rows, update_config, get_logging_config
from db.dashboard import get_dashboard_widgets, create_widget
from db.schema import create_base_table, refresh_card_cache
from imports.import_csv import parse_csv
from utils.validation import validation_sorter
from db.schema import load_field_schema, get_field_schema

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
def dashboard():
    widgets = get_dashboard_widgets()
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

@admin_bp.route('/admin/config')
def config_page():
    configs = get_config_rows()
    sections = {}
    for item in configs:
        sections.setdefault(item['section'], []).append(item)
    return render_template('config_admin.html', sections=sections)

@admin_bp.route('/admin/config/<path:key>', methods=['POST'])
def update_config_route(key):
    value = request.form.get('value', '')
    update_config(key, value)
    if key in get_logging_config():
        configure_logging(current_app)
    return redirect(url_for('admin.config_page'))

@admin_bp.route('/dashboard/widget', methods=['POST'])
def dashboard_create_widget():
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    content = data.get('content', '')
    widget_type = (data.get('widget_type') or '').strip()
    try:
        col_start = int(data.get('col_start', 1))
        col_span = int(data.get('col_span', 1))
        row_start = int(data.get('row_start', 1))
        row_span = int(data.get('row_span', 1))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid layout values'}), 400

    if not title or not widget_type:
        return jsonify({'error': 'Missing required fields'}), 400

    if widget_type not in {'value', 'table', 'chart'}:
        return jsonify({'error': 'Invalid widget type'}), 400

    widget_id = create_widget(
        title,
        content,
        widget_type,
        col_start,
        col_span,
        row_start,
        row_span,
    )

    if not widget_id:
        return jsonify({'error': 'Failed to create widget'}), 500

    return jsonify({'success': True, 'id': widget_id})

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
        success = create_base_table(table_name, description)
    except Exception as exc:
        current_app.logger.exception('Failed to create table %s: %s', table_name, exc)
        return jsonify({'error': str(exc)}), 400
    if not success:
        return jsonify({'error': 'Failed to create table'}), 400

    card_info, base_tables = refresh_card_cache()
    current_app.config['CARD_INFO'] = card_info
    current_app.config['BASE_TABLES'] = base_tables

    return jsonify({'success': True})

@admin_bp.route('/import', methods=['GET', 'POST'])
def import_records():
    schema = load_field_schema()
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
