from functools import wraps
from flask import request, abort
from db.validation import validate_table
from db.schema import get_field_schema
from db.records import get_all_records, count_records


def require_base_table(func):
    """Decorator to abort with 404 if the table does not exist."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        table = kwargs.get('table')
        if table is None and args:
            table = args[0]
        try:
            validate_table(table)
        except ValueError:
            abort(404)
        return func(*args, **kwargs)
    return wrapper


def parse_list_params(table):
    """Parse query parameters for list and export views."""
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


def build_list_context(table):
    """Return context dict used by list and API views."""
    params = parse_list_params(table)
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
        'has_filters': bool(filters),
    }
