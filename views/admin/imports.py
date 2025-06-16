import json
from flask import render_template, request, jsonify
from db.schema import get_field_schema
from imports.import_csv import parse_csv
from utils.validation import validation_sorter
from db.database import get_connection
from imports.tasks import process_import, init_import_table
from . import admin_bp


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
            (import_id,),
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
