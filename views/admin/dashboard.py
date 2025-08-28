import json
import logging
from flask import render_template, request, jsonify
from db.dashboard import (
    get_dashboard_widgets,
    create_widget,
    update_widget_layout,
    update_widget_styling,
    delete_widget,
    get_base_table_counts,
    get_top_numeric_values,
    get_filtered_records,
)


from . import admin_bp

logger = logging.getLogger(__name__)


@admin_bp.route('/dashboard')
def dashboard():
    widgets = get_dashboard_widgets()
    view = request.args.get("view") or "Dashboard"
    logger.debug(
        "Rendering dashboard view %s",
        view,
        extra={"view": view},
    )
    groups = sorted({(w.get("group") or "Dashboard") for w in widgets})
    for w in widgets:
        if w.get('widget_type') == 'table':
            try:
                w['parsed'] = json.loads(w.get('content') or '{}')
            except json.JSONDecodeError:
                w['parsed'] = {}
    return render_template(
        'dashboard.html', widgets=widgets, view=view, groups=groups
    )


@admin_bp.route('/dashboard/widget', methods=['POST'])
def dashboard_create_widget():
    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    widget_type = (data.get('widget_type') or '').strip()
    try:
        col_start = int(data.get('col_start', 1))
        col_span = int(data.get('col_span', 1))
        row_span = int(data.get('row_span', 1))
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid layout values'}), 400

    if not title or not widget_type:
        return jsonify({'error': 'Missing required fields'}), 400

    if widget_type not in {'value', 'table', 'chart'}:
        return jsonify({'error': 'Invalid widget type'}), 400

    content = data.get('content')
    if widget_type == 'chart':
        if content is None:
            content = {
                'chart_type': data.get('chart_type', 'bar'),
                'x_field': data.get('x_field'),
                'y_field': data.get('y_field'),
                'aggregation': data.get('aggregation', '')
            }
        if isinstance(content, str):
            try:
                json.loads(content)
            except json.JSONDecodeError:
                return jsonify({'error': 'Invalid JSON for content'}), 400
        else:
            content = json.dumps(content)
    else:
        if isinstance(content, (dict, list)):
            content = json.dumps(content)
        if content is None:
            content = ''

    group = (data.get('group') or 'Dashboard').strip() or 'Dashboard'
    widget_id = create_widget(
        title,
        content,
        widget_type,
        col_start,
        col_span,
        None,
        row_span,
        group,
    )

    if not widget_id:
        return jsonify({'error': 'Failed to create widget'}), 500

    logger.info(
        "Created dashboard widget %s type=%s",
        widget_id,
        widget_type,
        extra={"widget_id": widget_id, "widget_type": widget_type},
    )
    return jsonify({'success': True, 'id': widget_id})


@admin_bp.route('/dashboard/layout', methods=['POST'])
def dashboard_update_layout():
    data = request.get_json(silent=True)
    if not data or not isinstance(data.get('layout'), list):
        return jsonify({'error': 'Invalid JSON or missing `layout`'}), 400
    layout_items = data['layout']
    updated = update_widget_layout(layout_items)
    logger.info(
        "Updated dashboard layout for %d items",
        len(layout_items),
        extra={"item_count": len(layout_items)},
    )
    return jsonify({'success': True, 'updated': updated})


@admin_bp.route('/dashboard/style', methods=['POST'])
def dashboard_update_style():
    data = request.get_json(silent=True) or {}
    widget_id = data.get('widget_id')
    styling = data.get('styling')
    if widget_id is None or not isinstance(styling, dict):
        return jsonify({'error': 'Invalid data'}), 400
    success = update_widget_styling(widget_id, styling)
    logger.info(
        "Updated dashboard styling widget=%s success=%s",
        widget_id,
        bool(success),
        extra={"widget_id": widget_id, "success": bool(success)},
    )
    return jsonify({'success': bool(success)})


@admin_bp.route('/dashboard/widget/<int:widget_id>/delete', methods=['POST'])
def dashboard_delete_widget(widget_id):
    """Delete a dashboard widget."""
    success = delete_widget(widget_id)
    if not success:
        return jsonify({'error': 'Failed to delete widget'}), 500
    logger.info(
        "Deleted dashboard widget %s",
        widget_id,
        extra={"widget_id": widget_id},
    )
    return jsonify({'success': True})


@admin_bp.route('/dashboard/base-count')
def dashboard_base_count():
    """Return counts for all base tables."""
    data = get_base_table_counts()
    logger.debug("Returning base table counts", extra={"route": "dashboard_base_count"})
    return jsonify(data)


@admin_bp.route('/dashboard/top-numeric')
def dashboard_top_numeric():
    """Return top or bottom numeric values from a table."""
    table = request.args.get('table')
    field = request.args.get('field')
    try:
        limit = int(request.args.get('limit', 10))
    except (TypeError, ValueError):
        limit = 10
    direction = request.args.get('direction', 'desc')
    try:
        data = get_top_numeric_values(
            table,
            field,
            limit=limit,
            ascending=(direction == 'asc'),
        )
    except ValueError:
        return jsonify([]), 400
    logger.debug(
        "Top numeric for %s.%s limit=%s direction=%s",
        table,
        field,
        limit,
        direction,
        extra={
            "table": table,
            "field": field,
            "limit": limit,
            "direction": direction,
        },
    )
    return jsonify(data)


@admin_bp.route('/dashboard/filtered-records')
def dashboard_filtered_records():
    """Return filtered records from a table."""
    table = request.args.get('table')
    search = request.args.get('search')
    order_by = request.args.get('order_by')
    try:
        limit = int(request.args.get('limit', 10))
    except (TypeError, ValueError):
        limit = 10
    try:
        data = get_filtered_records(table, filters=search, order_by=order_by, limit=limit)
    except ValueError:
        return jsonify([]), 400
    logger.debug(
        "Filtered records for %s search=%s order_by=%s limit=%s",
        table,
        search,
        order_by,
        limit,
        extra={
            "table": table,
            "search": search,
            "order_by": order_by,
            "limit": limit,
        },
    )
    return jsonify(data)
