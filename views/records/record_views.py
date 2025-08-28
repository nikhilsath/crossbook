import json
import logging
import sqlite3
from flask import Blueprint, render_template, abort, request, redirect, url_for, jsonify, current_app

from db.records import (
    get_record_by_id,
    create_record,
    delete_record,
    count_nonnull as db_count_nonnull,
    field_distribution,
)
from db.edit_history import (
    get_edit_history,
    get_edit_entry,
    revert_edit,
)
from db.relationships import get_related_records, add_relationship, remove_relationship
from werkzeug.exceptions import HTTPException
from db.edit_fields import add_column_to_table, add_field_to_schema, drop_column_from_table, remove_field_from_schema
from db.schema import (
    get_field_schema,
    update_layout as db_update_layout,
    update_field_styling as db_update_field_styling,
)
from db.dashboard import sum_field as db_sum_field
from db.config import get_layout_defaults
from db.config import get_relationship_visibility, update_relationship_visibility
from utils.field_registry import get_field_type, get_type_size_map

records_bp = Blueprint('records', __name__)
from utils.records_helpers import require_base_table
from utils.record_ops import update_record_field, bulk_update_records

logger = logging.getLogger(__name__)


@records_bp.route('/<table>/<int:record_id>')
@require_base_table
def detail_view(table, record_id):
    record = get_record_by_id(table, record_id)
    if not record:
        abort(404)
    existing_related = get_related_records(table, record_id)
    base_tables = current_app.config['BASE_TABLES']
    card_info = current_app.config.get('CARD_INFO', [])
    label_map = {c['table_name']: c['display_name'] for c in card_info}
    visibility_all = get_relationship_visibility().get(table, {})
    related = []
    for tbl in base_tables:
        if tbl == table:
            continue
        group = existing_related.get(
            tbl,
            {"label": label_map.get(tbl, tbl.capitalize()), "items": []},
        )
        vis = visibility_all.get(tbl, {})
        related.append((tbl, group, vis))
    field_schema = get_field_schema()
    raw_layout = field_schema.get(table, {})
    field_schema_layout = {field: meta.get('layout', {}) for field, meta in raw_layout.items()}
    logger.debug(
        "[DETAIL] Using layout: %s",
        field_schema_layout,
        extra={"table": table, "record_id": record_id},
    )
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
        field_layout_defaults=field_layout_defaults,
        relationship_visibility=visibility_all
    )


@records_bp.route('/<table>/<int:record_id>/add-field', methods=['POST'])
@require_base_table
def add_field_route(table, record_id):
    try:
        field_name = request.form['field_name']
        logger.debug(
            'add_field_route start: table=%r, record_id=%r, form=%r',
            table,
            record_id,
            dict(request.form),
            extra={"table": table, "record_id": record_id},
        )
        logger.info(
            'table=%s record_id=%s form=%s',
            table,
            record_id,
            dict(request.form),
            extra={"table": table, "record_id": record_id},
        )
        field_type = request.form['field_type']
        if field_type == 'title':
            return 'Cannot add additional title field', 400
        field_options_raw = request.form.get('field_options', '')
        foreign_key = request.form.get('foreign_key_target', None)
        styling_raw = request.form.get('styling')
        field_options = [opt.strip() for opt in field_options_raw.split(',') if opt.strip()] if field_options_raw else []
        styling = json.loads(styling_raw) if styling_raw else None
        add_column_to_table(table, field_name, field_type)
        logger.info(
            'Returned from add_column_to_table for field %s',
            field_name,
            extra={"table": table, "record_id": record_id, "field": field_name},
        )
        add_field_to_schema(
            table=table,
            field_name=field_name,
            field_type=field_type,
            field_options=field_options,
            foreign_key=foreign_key,
            styling=styling,
        )
        logger.info(
            'Added column to %s: field=%r type=%r',
            table,
            field_name,
            field_type,
            extra={"table": table, "field": field_name, "type": field_type},
        )
        return redirect(url_for('records.detail_view', table=table, record_id=record_id))
    except json.JSONDecodeError as e:
        logger.exception(
            'add_field_route invalid styling JSON',
            extra={"table": table, "record_id": record_id},
        )
        return 'Invalid styling data', 400
    except sqlite3.DatabaseError as e:
        logger.exception(
            'add_field_route database error: %s',
            e,
            extra={"table": table, "record_id": record_id, "error": str(e)},
        )
        return 'Server error', 500
    except ValueError as e:
        logger.exception(
            'add_field_route validation failed',
            extra={"table": table, "record_id": record_id, "error": str(e)},
        )
        return str(e), 400


@records_bp.route('/<table>/count-nonnull')
@require_base_table
def count_nonnull(table):
    field = request.args.get('field')
    try:
        count = db_count_nonnull(table, field)
    except ValueError:
        logger.warning(
            'count_nonnull invalid field',
            exc_info=True,
            extra={"table": table, "field": field},
        )
        return jsonify({'count': 0}), 400
    return jsonify({'count': count})


@records_bp.route('/<table>/sum-field')
@require_base_table
def sum_field_route(table):
    field = request.args.get('field')
    try:
        result = db_sum_field(table, field)
    except ValueError:
        logger.warning(
            'sum_field invalid field',
            exc_info=True,
            extra={"table": table, "field": field},
        )
        return jsonify({'sum': 0}), 400
    return jsonify({'sum': result})


@records_bp.route('/<table>/field-distribution')
@require_base_table
def field_distribution_route(table):
    field = request.args.get('field')
    try:
        counts = field_distribution(table, field)
    except ValueError:
        logger.warning(
            'field_distribution invalid field',
            exc_info=True,
            extra={"table": table, "field": field},
        )
        return jsonify({}), 400
    return jsonify(counts)


@records_bp.route('/<table>/<int:record_id>/remove-field', methods=['POST'])
@require_base_table
def remove_field_route(table, record_id):
    field_name = request.form.get('field_name')
    fmeta = get_field_schema().get(table, {}).get(field_name)
    if not field_name or fmeta is None or fmeta['type'] == 'hidden' or field_name == 'id':
        abort(400, 'Invalid field')
    drop_column_from_table(table, field_name)
    remove_field_from_schema(table, field_name)
    return redirect(url_for('records.detail_view', table=table, record_id=record_id))


@records_bp.route('/<table>/<int:record_id>/update', methods=['POST'])
@require_base_table
def update_field(table, record_id):
    field = request.form.get('field')
    if not field:
        abort(400, 'Field missing')
    raw_value = (
        request.form.getlist('new_value[]')
        if request.form.getlist('new_value[]')
        else request.form.get('new_value_override') or request.form.get('new_value', '')
    )
    try:
        new_value = update_record_field(table, record_id, field, raw_value)
    except ValueError as e:
        logger.exception(
            'update_field validation failed',
            extra={"table": table, "record_id": record_id, "field": field},
        )
        abort(400, str(e))
    except RuntimeError:
        logger.exception(
            'update_field database update failed',
            extra={"table": table, "record_id": record_id, "field": field},
        )
        abort(500, 'Database update failed')
    logger.debug(
        'update_field: table=%s id=%s field=%s value=%r',
        table,
        record_id,
        field,
        new_value,
        extra={"table": table, "record_id": record_id, "field": field},
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"success": True, "new_value": new_value})

    return redirect(url_for('records.detail_view', table=table, record_id=record_id))


@records_bp.route('/<table>/bulk-update', methods=['POST'])
@require_base_table
def bulk_update(table):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    ids = data.get('ids')
    field = data.get('field')
    value = data.get('value')
    if not isinstance(ids, list) or not field:
        return jsonify({'error': 'Missing ids or field'}), 400
    try:
        updated = bulk_update_records(table, ids, field, value)
    except ValueError as e:
        logger.exception(
            'bulk_update validation failed',
            extra={"table": table, "field": field, "error": str(e)},
        )
        return jsonify({'error': str(e)}), 400
    return jsonify({'success': True, 'updated': updated})


@records_bp.route('/relationship', methods=['POST'])
def manage_relationship():
    data = request.get_json()
    logger.debug(
        'manage_relationship request: %s',
        data,
        extra={"action": data.get('action'), "table_a": data.get('table_a'), "table_b": data.get('table_b')},
    )
    action = data.get('action')
    table_a = data.get('table_a')
    id_a = data.get('id_a')
    table_b = data.get('table_b')
    id_b = data.get('id_b')
    two_way = data.get('two_way', True)
    try:
        if action == 'add':
            success = add_relationship(
                table_a, id_a, table_b, id_b, two_way=bool(two_way)
            )
        elif action == 'remove':
            success = remove_relationship(table_a, id_a, table_b, id_b)
        else:
            abort(400, 'Invalid action')
    except HTTPException:
        raise
    except ValueError as e:
        logger.warning(
            'manage_relationship validation failed action=%s %s:%s -> %s:%s',
            action,
            table_a,
            id_a,
            table_b,
            id_b,
            extra={
                "action": action,
                "table_a": table_a,
                "id_a": id_a,
                "table_b": table_b,
                "id_b": id_b,
                "error": str(e),
            },
            exc_info=True,
        )
        abort(400, str(e))
    except Exception:
        logger.exception(
            'Unexpected exception in manage_relationship action=%s %s:%s -> %s:%s',
            action,
            table_a,
            id_a,
            table_b,
            id_b,
            extra={
                "action": action,
                "table_a": table_a,
                "id_a": id_a,
                "table_b": table_b,
                "id_b": id_b,
            },
        )
        abort(500, 'Failed to modify relationship')
    if not success:
        logger.error(
            'manage_relationship failed action=%s %s:%s -> %s:%s',
            action,
            table_a,
            id_a,
            table_b,
            id_b,
            extra={
                "action": action,
                "table_a": table_a,
                "id_a": id_a,
                "table_b": table_b,
                "id_b": id_b,
            },
            exc_info=True,
        )
        abort(500, 'Failed to modify relationship')
    else:
        logger.info(
            'manage_relationship %s %s:%s %s:%s',
            action,
            table_a,
            id_a,
            table_b,
            id_b,
            extra={
                "action": action,
                "table_a": table_a,
                "id_a": id_a,
                "table_b": table_b,
                "id_b": id_b,
            },
        )
    return {'success': True}


@records_bp.route('/<table>/new', methods=['GET', 'POST'])
@require_base_table
def create_record_route(table):
    fields = get_field_schema().get(table, {})
    if request.method == 'POST':
        record_id = create_record(table, request.form)
        if record_id:
            return redirect(f'/{table}/{record_id}')
        else:
            abort(500, 'Failed to create record')
    return render_template('modals/new_record_modal.html', table=table, fields=fields)


@records_bp.route('/<table>/<int:record_id>/delete', methods=['POST'])
@require_base_table
def delete_record_route(table, record_id):
    success = delete_record(table, record_id)
    if not success:
        abort(500, 'Failed to delete record')
    return redirect(url_for('records.list_view', table=table))


@records_bp.route('/<table>/<int:record_id>/undo/<int:edit_id>', methods=['POST'])
@require_base_table
def undo_edit_route(table, record_id, edit_id):
    entry = get_edit_entry(edit_id)
    if not entry or entry['table_name'] != table or entry['record_id'] != record_id:
        abort(404)
    success = revert_edit(entry)
    if not success:
        abort(500, 'Undo failed')
    return jsonify({'success': True})



@records_bp.route('/<table>/layout', methods=['POST'])
@require_base_table
def update_layout(table):
    data = request.get_json(silent=True)
    if not data or not isinstance(data.get('layout'), list):
        return jsonify({'error': 'Invalid JSON or missing `layout`'}), 400
    layout_items = data['layout']
    try:
        updated = db_update_layout(table, layout_items)
    except ValueError as e:
        logger.exception(
            'update_layout validation failed',
            extra={"table": table, "error": str(e)},
        )
        return jsonify({'error': str(e)}), 400
    logger.info(
        '[layout] update_layout %s updated=%s',
        table,
        updated,
        extra={"table": table, "updated": updated},
    )
    logger.debug(
        '[layout] payload %s',
        layout_items,
        extra={"table": table},
    )
    return jsonify({'success': True, 'updated': updated})


@records_bp.route('/<table>/style', methods=['POST'])
@require_base_table
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
        logger.exception(
            'update_style validation failed',
            extra={"table": table, "field": field, "error": str(e)},
        )
        return jsonify({'error': str(e)}), 400
    logger.info(
        '[style] update_style %s.%s success=%s',
        table,
        field,
        bool(success),
        extra={"table": table, "field": field, "success": bool(success)},
    )
    logger.debug(
        '[style] payload %s',
        styling,
        extra={"table": table, "field": field},
    )
    return jsonify({'success': bool(success)})


@records_bp.route('/<table>/relationships', methods=['POST'])
@require_base_table
def update_relationships(table):
    """Update relationship visibility configuration for a table."""
    data = request.get_json(silent=True) or {}
    visibility = data.get('visibility')
    if not isinstance(visibility, dict):
        return jsonify({'error': 'Invalid JSON'}), 400
    try:
        update_relationship_visibility(table, visibility)
    except sqlite3.DatabaseError as e:
        current_app.logger.exception(
            '[relationships] update failed: %s',
            e,
            extra={"table": table, "error": str(e)},
        )
        return jsonify({'error': 'update failed'}), 500
    return jsonify({'success': True})

# Ensure list view routes are registered after blueprint is defined
from . import list_views  # noqa: E402,F401
