import json
import csv
import io
from flask import Blueprint, render_template, abort, request, redirect, url_for, jsonify, current_app, Response
from db.database import get_connection
from db.validation import validate_table
from db.records import (
    get_all_records,
    get_record_by_id,
    update_field_value,
    create_record,
    delete_record,
    count_nonnull as db_count_nonnull,
    field_distribution,
    count_records,
    append_edit_log,
    get_edit_history,
    get_edit_entry,
    revert_edit,
)
from db.relationships import get_related_records, add_relationship, remove_relationship
from db.edit_fields import add_column_to_table, add_field_to_schema, drop_column_from_table, remove_field_from_schema
from db.schema import (
    get_field_schema,
    update_layout as db_update_layout,
    update_field_styling as db_update_field_styling,
    get_title_field,
)
from db.dashboard import sum_field as db_sum_field
from db.config import get_layout_defaults
from utils.field_registry import get_field_type, get_type_size_map

records_bp = Blueprint('records', __name__)


def _parse_list_params(table):
    """Parse query parameters for list/export routes."""
    base_tables = current_app.config['BASE_TABLES']
    if table not in base_tables:
        abort(404)
    fields = list(get_field_schema()[table].keys())
    search = request.args.get('search', '').strip()

    raw_args = request.args.to_dict(flat=False)
    field_map = {f.lower(): f for f in fields}
    normalized = {field_map.get(k.lower(), k): v for k, v in raw_args.items()}

    filters = {
        k: v
        for k, v in normalized.items()
        if k in fields
        or (k.endswith('_min') and k[:-4] in fields)
        or (k.endswith('_max') and k[:-4] in fields)
        or (k.endswith('_start') and k[:-6] in fields)
        or (k.endswith('_end') and k[:-4] in fields)
    }

    ops = {
        k[:-3]: (v[0] if isinstance(v, list) else v)
        for k, v in normalized.items()
        if k.endswith('_op') and k[:-3] in fields
    }

    modes = {
        k[:-5]: (v[0] if isinstance(v, list) else v)
        for k, v in normalized.items()
        if k.endswith('_mode') and k[:-5] in fields
    }

    sort_field = request.args.get('sort')
    direction = request.args.get('dir', 'asc')

    return {
        'fields': fields,
        'search': search,
        'filters': filters,
        'ops': ops,
        'modes': modes,
        'sort_field': sort_field,
        'direction': direction,
    }

def _build_list_context(table):
    params = _parse_list_params(table)
    fields = params['fields']
    search = params['search']
    filters = params['filters']
    ops = params['ops']
    modes = params['modes']
    sort_field = params['sort_field']
    direction = params['direction']
    page = int(request.args.get('page', 1))
    per_page = 500
    offset = (page - 1) * per_page
    records = get_all_records(
        table,
        search=search,
        filters=filters,
        ops=ops,
        modes=modes,
        sort_field=sort_field,
        direction=direction,
        limit=per_page,
        offset=offset,
    )
    total_count = count_records(table, search=search, filters=filters, ops=ops, modes=modes)
    args_without_page = request.args.to_dict(flat=False)
    args_without_page.pop('page', None)
    from urllib.parse import urlencode
    base_qs = urlencode(args_without_page, doseq=True)
    args_no_sort = dict(args_without_page)
    args_no_sort.pop('sort', None)
    args_no_sort.pop('dir', None)
    base_qs_no_sort = urlencode(args_no_sort, doseq=True)
    total_pages = (total_count + per_page - 1) // per_page
    start = offset + 1 if total_count else 0
    end = min(offset + len(records), total_count)

    return {
        'table': table,
        'fields': fields,
        'records': records,
        'sort_field': sort_field,
        'direction': direction,
        'page': page,
        'total_pages': total_pages,
        'total_count': total_count,
        'start': start,
        'end': end,
        'per_page': per_page,
        'base_qs': base_qs,
        'base_qs_no_sort': base_qs_no_sort,
    }

@records_bp.route('/<table>')
def list_view(table):
    ctx = _build_list_context(table)
    if request.accept_mimetypes.best == 'application/json':
        rows = render_template('_record_rows.html', **ctx)
        pager = render_template('_pagination.html', **ctx)
        count = render_template('_record_count.html', **ctx)
        filters = render_template('_filter_chips.html', **ctx)
        ctx.update({'rows_html': rows, 'pagination_html': pager,
                    'count_html': count, 'filters_html': filters})
        return jsonify(ctx)
    return render_template('list_view.html', request=request, **ctx)


@records_bp.route('/api/<table>/list')
def api_list(table):
    """Return basic id/label info for records in the table."""
    try:
        validate_table(table)
    except ValueError:
        abort(404)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info({table})")
        cols = [r[1] for r in cur.fetchall()]
        if not cols:
            return jsonify([])
        title_field = get_title_field(table)
        if title_field:
            label_field = title_field
        elif table in cols:
            label_field = table
        elif len(cols) > 1:
            label_field = cols[1]
        else:
            label_field = cols[0]
        cur.execute(f"SELECT id, {label_field} FROM {table}")
        rows = cur.fetchall()

    return jsonify([{'id': r[0], 'label': r[1]} for r in rows])


@records_bp.route('/api/<table>/records')
def api_records(table):
    ctx = _build_list_context(table)
    rows = render_template('_record_rows.html', **ctx)
    pager = render_template('_pagination.html', **ctx)
    count = render_template('_record_count.html', **ctx)
    filters = render_template('_filter_chips.html', **ctx)
    ctx.update({'rows_html': rows, 'pagination_html': pager,
                'count_html': count, 'filters_html': filters})
    return jsonify(ctx)


@records_bp.route('/<table>/export')
def export_csv(table):
    """Stream CSV of records using current filters and search."""
    params = _parse_list_params(table)
    fields = [f for f in params['fields'] if not f.startswith('_')]
    records = get_all_records(
        table,
        search=params['search'],
        filters=params['filters'],
        ops=params['ops'],
        modes=params['modes'],
        sort_field=params['sort_field'],
        direction=params['direction'],
    )

    def generate():
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(fields)
        yield buf.getvalue()
        buf.seek(0)
        buf.truncate(0)
        for row in records:
            writer.writerow([row.get(f, '') for f in fields])
            yield buf.getvalue()
            buf.seek(0)
            buf.truncate(0)

    filename = f"{table}.csv"
    return Response(
        generate(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )

@records_bp.route('/<table>/<int:record_id>')
def detail_view(table, record_id):
    try:
        validate_table(table)
    except ValueError:
        abort(404)

    record = get_record_by_id(table, record_id)
    if not record:
        abort(404)
    related = get_related_records(table, record_id)
    field_schema = get_field_schema()
    raw_layout = field_schema.get(table, {})
    field_schema_layout = {field: meta.get('layout', {}) for field, meta in raw_layout.items()}
    current_app.logger.debug("[DETAIL] Using layout: %s", field_schema_layout)
    history = get_edit_history(table, record_id)
    defaults = get_layout_defaults() or {}
    width_overrides = defaults.get('width', {})
    height_overrides = defaults.get('height', {})
    size_map = get_type_size_map()
    field_layout_defaults = {}
    for ftype in set(list(size_map.keys()) + list(width_overrides.keys()) + list(height_overrides.keys())):
        ft = get_field_type(ftype)
        base_width, base_height = size_map.get(
            ftype,
            (
                ft.default_width if ft else 6,
                ft.default_height if ft else 4,
            ),
        )
        field_layout_defaults[ftype] = (
            width_overrides.get(ftype, base_width),
            height_overrides.get(ftype, base_height),
        )
    return render_template(
        'detail_view.html',
        table=table,
        record=record,
        related=related,
        edit_history=history,
        field_schema_layout=field_schema_layout,
        field_layout_defaults=field_layout_defaults
    )

@records_bp.route('/<table>/<int:record_id>/add-field', methods=['POST'])
def add_field_route(table, record_id):
    try:
        # Ensure table exists in schema
        validate_table(table)

        field_name = request.form['field_name']
        current_app.logger.debug(
            'add_field_route start: table=%r, record_id=%r, form=%r', table, record_id, dict(request.form)
        )
        current_app.logger.info('table=%s record_id=%s form=%s', table, record_id, dict(request.form))
        field_type = request.form['field_type']
        if field_type == 'title':
            return 'Cannot add additional title field', 400
        field_options_raw = request.form.get('field_options', '')
        foreign_key = request.form.get('foreign_key_target', None)
        styling_raw = request.form.get('styling')
        field_options = [opt.strip() for opt in field_options_raw.split(',') if opt.strip()] if field_options_raw else []
        styling = json.loads(styling_raw) if styling_raw else None
        add_column_to_table(table, field_name, field_type)
        current_app.logger.info('Returned from add_column_to_table for field %s', field_name)
        add_field_to_schema(
            table=table,
            field_name=field_name,
            field_type=field_type,
            field_options=field_options,
            foreign_key=foreign_key,
            styling=styling,
        )
        current_app.logger.info('Added column to %s: field=%r type=%r', table, field_name, field_type)
        return redirect(url_for('records.detail_view', table=table, record_id=record_id))
    except ValueError as e:
        current_app.logger.warning('add_field_route validation failed: %s', e)
        return str(e), 400
    except Exception as e:
        current_app.logger.exception('add_field_route error: %s', e)
        return 'Server error', 500

@records_bp.route('/<table>/count-nonnull')
def count_nonnull(table):
    field = request.args.get('field')
    try:
        count = db_count_nonnull(table, field)
    except ValueError:
        return jsonify({'count': 0}), 400
    return jsonify({'count': count})

@records_bp.route('/<table>/sum-field')
def sum_field_route(table):
    field = request.args.get('field')
    try:
        result = db_sum_field(table, field)
    except ValueError:
        return jsonify({'sum': 0}), 400
    return jsonify({'sum': result})


@records_bp.route('/<table>/field-distribution')
def field_distribution_route(table):
    field = request.args.get('field')
    try:
        counts = field_distribution(table, field)
    except ValueError:
        return jsonify({}), 400
    return jsonify(counts)

@records_bp.route('/<table>/<int:record_id>/remove-field', methods=['POST'])
def remove_field_route(table, record_id):
    field_name = request.form.get('field_name')
    fmeta = get_field_schema().get(table, {}).get(field_name)
    if not field_name or fmeta is None or fmeta['type'] == 'hidden' or field_name == 'id':
        abort(400, 'Invalid field')
    drop_column_from_table(table, field_name)
    remove_field_from_schema(table, field_name)
    return redirect(url_for('records.detail_view', table=table, record_id=record_id))

@records_bp.route('/<table>/<int:record_id>/update', methods=['POST'])
def update_field(table, record_id):
    field = request.form.get('field')
    if not field:
        abort(400, 'Field missing')
    fmeta = get_field_schema().get(table, {}).get(field)
    if not fmeta:
        abort(400, 'Unknown field')
    ftype = fmeta['type']
    if ftype in ('multi_select', 'foreign_key'):
        vals = request.form.getlist('new_value[]')
        new_value = ', '.join(vals)
    else:
        raw = request.form.get('new_value_override') or request.form.get('new_value', '')
        if ftype == 'boolean':
            new_value = '1' if raw.lower() in ('1','on','true') else '0'
        elif ftype == 'number':
            try:
                new_value = int(raw)
            except ValueError:
                new_value = 0
        else:
            new_value = raw
        if ftype == 'textarea':
            from utils.html_sanitizer import sanitize_html
            new_value = sanitize_html(new_value)
    current_app.logger.debug('update_field: table=%s id=%s field=%s value=%r', table, record_id, field, new_value)
    prev_record = get_record_by_id(table, record_id)
    prev_value = prev_record.get(field) if prev_record else None
    success = update_field_value(table, record_id, field, new_value)
    if not success:
        abort(500, 'Database update failed')
    current_app.logger.info('Field updated for %s id=%s: %s -> %r', table, record_id, field, new_value)
    if prev_record is not None and str(prev_value) != str(new_value):
        append_edit_log(
            table,
            record_id,
            field,
            str(prev_value),
            str(new_value),
        )
    return redirect(url_for('records.detail_view', table=table, record_id=record_id))


@records_bp.route('/<table>/bulk-update', methods=['POST'])
def bulk_update(table):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    ids = data.get('ids')
    field = data.get('field')
    value = data.get('value')
    if not isinstance(ids, list) or not field:
        return jsonify({'error': 'Missing ids or field'}), 400
    schema = get_field_schema().get(table, {})
    fmeta = schema.get(field)
    if fmeta is None:
        return jsonify({'error': 'Unknown field'}), 400
    ftype = fmeta['type']
    if ftype == 'boolean':
        value = '1' if str(value).lower() in ('1', 'true', 'on') else '0'
    elif ftype == 'number':
        try:
            value = int(value)
        except (TypeError, ValueError):
            value = 0
    elif ftype in ('multi_select', 'foreign_key'):
        if isinstance(value, list):
            value = ', '.join([str(v) for v in value])
        elif value is None:
            value = ''
    elif ftype == 'textarea':
        from utils.html_sanitizer import sanitize_html
        value = sanitize_html(value or '')

    updated = 0
    for rid in ids:
        if update_field_value(table, rid, field, value):
            append_edit_log(table, rid, field, None, str(value))
            updated += 1
    return jsonify({'success': True, 'updated': updated})

@records_bp.route('/relationship', methods=['POST'])
def manage_relationship():
    data = request.get_json()
    current_app.logger.debug('manage_relationship request: %s', data)
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
                f'relation_{table_b}',
                None,
                str(id_b),
            )
    elif action == 'remove':
        success = remove_relationship(table_a, id_a, table_b, id_b)
        if success:
            append_edit_log(
                table_a,
                id_a,
                f'relation_{table_b}',
                str(id_b),
                None,
            )
    else:
        abort(400, 'Invalid action')
    if not success:
        current_app.logger.error('manage_relationship failed action=%s %s:%s -> %s:%s', action, table_a, id_a, table_b, id_b)
        abort(500, 'Failed to modify relationship')
    else:
        current_app.logger.info('manage_relationship %s %s:%s %s:%s', action, table_a, id_a, table_b, id_b)
    return {'success': True}

@records_bp.route('/<table>/new', methods=['GET', 'POST'])
def create_record_route(table):
    base_tables = current_app.config['BASE_TABLES']
    if table not in base_tables:
        abort(404)
    fields = get_field_schema().get(table, {})
    if request.method == 'POST':
        record_id = create_record(table, request.form)
        if record_id:
            return redirect(f'/{table}/{record_id}')
        else:
            abort(500, 'Failed to create record')
    return render_template('new_record.html', table=table, fields=fields)

@records_bp.route('/<table>/<int:record_id>/delete', methods=['POST'])
def delete_record_route(table, record_id):
    base_tables = current_app.config['BASE_TABLES']
    if table not in base_tables:
        abort(404)
    success = delete_record(table, record_id)
    if not success:
        abort(500, 'Failed to delete record')
    return redirect(url_for('records.list_view', table=table))


@records_bp.route('/<table>/<int:record_id>/undo/<int:edit_id>', methods=['POST'])
def undo_edit_route(table, record_id, edit_id):
    entry = get_edit_entry(edit_id)
    if not entry or entry['table_name'] != table or entry['record_id'] != record_id:
        abort(404)
    success = revert_edit(entry)
    if not success:
        abort(500, 'Undo failed')
    return jsonify({'success': True})

@records_bp.route('/<table>/layout', methods=['POST'])
def update_layout(table):
    data = request.get_json(silent=True)
    if not data or not isinstance(data.get('layout'), list):
        return jsonify({'error': 'Invalid JSON or missing `layout`'}), 400
    layout_items = data['layout']
    try:
        updated = db_update_layout(table, layout_items)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    current_app.logger.info('[layout] update_layout %s updated=%s', table, updated)
    current_app.logger.debug('[layout] payload %s', layout_items)
    return jsonify({'success': True, 'updated': updated})


@records_bp.route('/<table>/style', methods=['POST'])
def update_style(table):
    """Update styling information for a single field."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    field = data.get('field')
    styling = data.get('styling')
    if not field or styling is None:
        return jsonify({'error': 'Missing `field` or `styling`'}), 400
    if not isinstance(styling, dict):
        return jsonify({'error': '`styling` must be an object'}), 400
    try:
        success = db_update_field_styling(table, field, styling)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    current_app.logger.info('[style] update_style %s.%s success=%s', table, field, bool(success))
    current_app.logger.debug('[style] payload %s', styling)
    return jsonify({'success': bool(success)})
