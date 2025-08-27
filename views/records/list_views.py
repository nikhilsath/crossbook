import csv
import io
import logging
from flask import render_template, request, jsonify, Response

from db.database import get_connection
from db.schema import get_title_field
from db.records import get_all_records

from .record_views import records_bp
from utils.records_helpers import parse_list_params, build_list_context, require_base_table

logger = logging.getLogger(__name__)


@records_bp.route('/<table>')
@require_base_table
def list_view(table):
    logger.debug("Rendering list view for %s with args %s", table, dict(request.args))
    ctx = build_list_context(table)
    if request.accept_mimetypes.best == 'application/json':
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
    return render_template('list_view.html', request=request, **ctx)


@records_bp.route('/api/<table>/list')
@require_base_table
def api_list(table):
    """Return id and label info for records in the table."""
    search = request.args.get('search')
    limit = request.args.get('limit', type=int)
    logger.debug("api_list table=%s search=%s limit=%s", table, search, limit)

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


@records_bp.route('/api/<table>/records')
@require_base_table
def api_records(table):
    logger.debug("api_records table=%s args=%s", table, dict(request.args))
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


@records_bp.route('/<table>/export')
@require_base_table
def export_csv(table):
    """Stream CSV of records using current filters and search."""
    params = parse_list_params(table)
    fields = [f for f in params['fields'] if not f.startswith('_')]
    logger.info("Exporting CSV for %s fields=%s", table, fields)
    ids_param = request.args.getlist('ids') or request.args.get('ids', '')
    if isinstance(ids_param, str):
        ids = [i for i in ids_param.split(',') if i]
    else:
        ids = ids_param
    ids = [int(i) for i in ids if str(i).isdigit()]
    if ids:
        records = get_all_records(
            table,
            filters={'id': ids},
            ops={'id': 'equals'},
            modes={'id': 'any'},
        )
    else:
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
