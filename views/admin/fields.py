import logging
import sqlite3
from flask import render_template, current_app

from db.schema import get_field_schema
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
                logger.exception('Failed counting %s.%s', table, field)
                nn = 0
            fields.append({'name': field, 'type': meta.get('type'), 'count': nn})
        table_data[table] = fields
    return render_template('admin/fields_admin.html', tables=table_data)
