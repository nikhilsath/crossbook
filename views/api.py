import logging
from flask import Blueprint, request, jsonify, render_template
from db.database import get_connection
from db.schema import get_title_field
from utils.field_registry import FIELD_TYPES
from utils.records_helpers import build_list_context, require_base_table

api_bp = Blueprint('api', __name__, url_prefix='/api')

logger = logging.getLogger(__name__)

@api_bp.route('/field-types')
def api_field_types():
    """Return list of available field types."""
    return jsonify(list(FIELD_TYPES.keys()))


@api_bp.route('/<table>/list')
@require_base_table
def api_list(table):
    """Return id and label info for records in the table."""
    search = request.args.get('search')
    limit = request.args.get('limit', type=int)

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

        sql = f"SELECT id, {label_field} FROM {table}"
        params = []
        if search is not None:
            sql += f" WHERE {label_field} LIKE ?"
            params.append(f"%{search}%")
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        cur.execute(sql, params)
        rows = cur.fetchall()

    return jsonify([{'id': r[0], 'label': r[1]} for r in rows])


@api_bp.route('/<table>/records')
@require_base_table
def api_records(table):
    ctx = build_list_context(table)
    rows = render_template('_record_rows.html', **ctx)
    pager = render_template('_pagination.html', **ctx)
    count = render_template('_record_count.html', **ctx)
    filters = render_template('_filter_chips.html', **ctx)
    ctx.update({
        'rows_html': rows,
        'pagination_html': pager,
        'count_html': count,
        'filters_html': filters,
    })
    return jsonify(ctx)
