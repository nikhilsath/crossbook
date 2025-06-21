import csv
import io
import logging
from flask import render_template, request, jsonify, Response

from db.records import get_all_records

from .record_views import records_bp
from utils.records_helpers import parse_list_params, build_list_context, require_base_table

logger = logging.getLogger(__name__)


@records_bp.route('/<table>')
@require_base_table
def list_view(table):
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




@records_bp.route('/<table>/export')
@require_base_table
def export_csv(table):
    """Stream CSV of records using current filters and search."""
    params = parse_list_params(table)
    fields = [f for f in params['fields'] if not f.startswith('_')]
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
