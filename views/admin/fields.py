import logging
import sqlite3
from flask import render_template, current_app, request, jsonify

from db.schema import get_field_schema, set_title_field
from db.records import count_nonnull
from . import admin_bp
from db.database import get_connection
from db.validation import validate_table, validate_field
from utils.validation import validation_sorter
from utils.field_registry import FIELD_TYPES

logger = logging.getLogger(__name__)

@admin_bp.route('/admin/fields')
def admin_fields():
    """Display tables and field info including not-null counts."""
    schema = get_field_schema()
    # Load readonly flags if the column exists
    readonly_map: dict[tuple[str, str], int] = {}
    try:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("PRAGMA table_info('field_schema')")
            cols = {r[1] for r in cur.fetchall()}
            if 'readonly' in cols:
                for tname, fname, ro in cur.execute(
                    "SELECT table_name, field_name, readonly FROM field_schema"
                ).fetchall():
                    readonly_map[(tname, fname)] = int(ro or 0)
    except Exception:
        # If anything goes wrong, default to all non-readonly
        readonly_map = {}
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
                'readonly': bool(readonly_map.get((table, field), 0)),
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


@admin_bp.route('/admin/fields/<table>/readonly', methods=['POST'])
def admin_set_readonly(table):
    """Toggle the readonly flag for a field in field_schema.

    Expects JSON or form with 'field' and optional 'readonly' (1/0 or true/false).
    """
    field = None
    readonly_val = None
    if request.is_json:
        payload = request.get_json(silent=True) or {}
        field = payload.get('field')
        readonly_val = payload.get('readonly')
    else:
        field = request.form.get('field')
        readonly_val = request.form.get('readonly')

    if field is None:
        return jsonify({'success': False, 'error': 'field required'}), 400

    try:
        validate_table(table)
        validate_field(table, field)
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    with get_connection() as conn:
        cur = conn.cursor()
        # Ensure column exists
        cur.execute("PRAGMA table_info('field_schema')")
        cols = {r[1] for r in cur.fetchall()}
        if 'readonly' not in cols:
            return jsonify({'success': False, 'error': "missing 'readonly' column"}), 400

        ro = 1 if str(readonly_val).lower() in {"1", "true", "on", "yes"} else 0
        try:
            cur.execute(
                "UPDATE field_schema SET readonly = ? WHERE table_name = ? AND field_name = ?",
                (ro, table, field),
            )
            conn.commit()
        except sqlite3.DatabaseError as exc:
            logger.exception(
                'Failed to update readonly flag',
                extra={'table': table, 'field': field, 'error': str(exc)},
            )
            return jsonify({'success': False, 'error': str(exc)}), 500

    return jsonify({'success': True, 'readonly': ro})


@admin_bp.route('/admin/fields/validate-type', methods=['POST'])
def admin_validate_field_type():
    """Validate existing field values against a proposed new type.

    Body JSON: {"table": str, "field": str, "new_type": str}
    Returns the validation report from utils.validation.validation_sorter.
    """
    data = request.get_json(silent=True) or {}
    table = data.get('table')
    field = data.get('field')
    new_type = data.get('new_type') or data.get('type')
    if not table or not field or not new_type:
        return jsonify({'error': 'table, field, and new_type are required'}), 400
    try:
        validate_table(table)
        validate_field(table, field)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # Fetch current non-null values
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            cur.execute(f'SELECT "{field}" FROM "{table}" WHERE "{field}" IS NOT NULL')
            rows = [str(r[0]) if r[0] is not None else '' for r in cur.fetchall()]
        except Exception as exc:
            logger.exception('Failed to fetch values for validation', extra={'table': table, 'field': field})
            return jsonify({'error': str(exc)}), 400

    report = validation_sorter(table, field, field, new_type, rows)
    return jsonify(report)


@admin_bp.route('/admin/fields/convert-type', methods=['POST'])
def admin_convert_field_type():
    """Convert a field's type in field_schema after validation.

    Body JSON: {"table": str, "field": str, "new_type": str}
    Performs server-side validation (no invalid values) before update.
    """
    data = request.get_json(silent=True) or {}
    table = data.get('table')
    field = data.get('field')
    new_type = data.get('new_type') or data.get('type')
    if not table or not field or not new_type:
        return jsonify({'error': 'table, field, and new_type are required'}), 400
    try:
        validate_table(table)
        validate_field(table, field)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    # Ensure new type is known
    if new_type not in FIELD_TYPES:
        return jsonify({'error': f'Unknown field type: {new_type}'}), 400

    # Prevent converting current title field away from text
    schema = get_field_schema()
    fmeta = schema.get(table, {}).get(field, {})
    if fmeta.get('title') and new_type != 'text':
        return jsonify({'error': 'Title field must remain type "text". Unset title first.'}), 400

    # Fetch current non-null values and validate with new type
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(f'SELECT "{field}" FROM "{table}" WHERE "{field}" IS NOT NULL')
        rows = [str(r[0]) if r[0] is not None else '' for r in cur.fetchall()]
        report = validation_sorter(table, field, field, new_type, rows)
        if int(report.get('invalid', 0)) > 0:
            return jsonify({'error': 'invalid_values', 'report': report}), 400

        # Update field_schema; null out options if the new type does not allow them
        allows_opts = bool(getattr(FIELD_TYPES.get(new_type), 'allows_options', False))
        try:
            if allows_opts:
                cur.execute(
                    'UPDATE field_schema SET field_type = ? WHERE table_name = ? AND field_name = ?',
                    (new_type, table, field),
                )
            else:
                cur.execute(
                    'UPDATE field_schema SET field_type = ?, field_options = NULL WHERE table_name = ? AND field_name = ?',
                    (new_type, table, field),
                )
            conn.commit()
        except sqlite3.DatabaseError as exc:
            logger.exception('Failed to convert field type', extra={'table': table, 'field': field, 'new_type': new_type})
            return jsonify({'error': str(exc)}), 500

    return jsonify({'success': True})
