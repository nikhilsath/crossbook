import logging
import sqlite3
from flask import render_template, current_app, request, jsonify

from db.schema import get_field_schema, set_title_field
from db.records import count_nonnull
from . import admin_bp

logger = logging.getLogger(__name__)

@admin_bp.route('/admin/fields')
def admin_fields():
    """Display tables and field info including not-null counts."""
    schema = get_field_schema()
    base_tables = current_app.config.get('BASE_TABLES', [])
    table_data: dict[str, list[dict]] = {}
    for table in base_tables:
        fields = []
        tbl_schema = schema.get(table, {})
        for field, meta in tbl_schema.items():
            if field == 'id' or meta.get('type') == 'hidden':
                continue
            try:
                nn = count_nonnull(table, field)
            except (sqlite3.DatabaseError, ValueError):
                logger.exception(
                    'Failed counting %s.%s',
                    table,
                    field,
                    extra={"table": table, "field": field},
                )
                nn = 0
            fields.append({
                'name': field,
                'type': meta.get('type'),
                'count': nn,
                'title': bool(meta.get('title')),
            })
        table_data[table] = fields
    return render_template('admin/fields_admin.html', tables=table_data)


@admin_bp.route('/admin/fields/<table>/title', methods=['POST'])
def admin_set_title_field(table):
    """Set the title field for a given table.

    Expects JSON or form data with key 'field'. Returns JSON {success: bool}.
    """
    field = None
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        field = payload.get('field')
    else:
        field = request.form.get('field')

    if not field:
        return jsonify({'success': False, 'error': 'field required'}), 400

    try:
        ok = set_title_field(table, field)
    except Exception as e:
        logger.exception('Failed to set title field', extra={'table': table, 'field': field})
        return jsonify({'success': False, 'error': str(e)}), 400
    return jsonify({'success': bool(ok)})
