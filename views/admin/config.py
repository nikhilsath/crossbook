import json
import os
import logging
from flask import (
    render_template,
    redirect,
    url_for,
    request,
    jsonify,
    current_app,
    session,
)
from werkzeug.utils import secure_filename
from logging_setup import configure_logging
from db.config import get_config_rows, update_config
from db.database import check_db_status, init_db_path
from db.bootstrap import initialize_database, ensure_default_configs
from db.schema import create_base_table
from utils.field_registry import FIELD_TYPES
from . import admin_bp, reload_app_state

logger = logging.getLogger(__name__)


@admin_bp.route('/admin/database')
def database_page():
    configs = get_config_rows()
    db_path = None
    db_status = 'missing'
    for item in configs:
        if item['key'] == 'db_path':
            db_path = item['value']
            db_status = check_db_status(db_path)
            break
    return render_template('admin/database_admin.html', db_path=db_path, db_status=db_status)


@admin_bp.route('/admin/config')
def config_page():
    configs = get_config_rows()
    sections = {}
    for item in configs:
        if item.get('type') == 'json':
            try:
                item['parsed'] = json.loads(item.get('value') or '{}')
            except Exception:
                item['parsed'] = {}
        if item['key'] == 'db_path':
            continue
        sections.setdefault(item['section'], []).append(item)
    return render_template('admin/config_admin.html', sections=sections)


@admin_bp.route('/admin/config/<path:key>', methods=['POST'])
def update_config_route(key):
    value = request.form.get('value', '')
    update_config(key, value)
    if key == 'db_path':
        reload_app_state()
    logging_keys = [row['key'] for row in get_config_rows('logging')]
    if key in logging_keys:
        configure_logging(current_app)
    return redirect(url_for('admin.config_page'))


@admin_bp.route('/admin/config/db', methods=['POST'])
def update_database_file():
    """Handle uploaded or newly created database files."""
    wants_json = 'application/json' in request.headers.get('Accept', '')
    if 'file' in request.files and request.files['file'].filename:
        file = request.files['file']
        filename = secure_filename(file.filename)
        if not filename.endswith('.db'):
            return redirect(url_for('admin.database_page'))
        save_path = os.path.join('data', filename)
        file.save(save_path)
        initialize_database(save_path)
        ensure_default_configs(save_path)
        update_config('db_path', save_path)
        reload_app_state()
        if wants_json:
            return jsonify({'db_path': save_path, 'status': check_db_status(save_path)})
        return redirect(url_for('admin.database_page'))

    name = request.form.get('create_name')
    if name:
        filename = secure_filename(name)
        if not filename.endswith('.db'):
            filename += '.db'
        save_path = os.path.join('data', filename)
        open(save_path, 'a').close()
        initialize_database(save_path)
        ensure_default_configs(save_path)
        update_config('db_path', save_path)
        reload_app_state()
        session['wizard_progress'] = {'database': True, 'skip_import': True}
        session.pop('wizard_complete', None)
        if wants_json:
            return jsonify({
                'db_path': save_path,
                'status': check_db_status(save_path),
                'redirect': url_for('wizard.wizard_start'),
            })
        return redirect(url_for('wizard.wizard_start'))
    if wants_json:
        return jsonify({'error': 'no_file'})
    return redirect(url_for('admin.database_page'))


@admin_bp.route('/api/field-types')
def api_field_types():
    """Return list of available field types."""
    return jsonify(list(FIELD_TYPES.keys()))


@admin_bp.route('/add-table', methods=['POST'])
def add_table():
    data = request.get_json(silent=True) or {}
    table_name = (data.get('table_name') or '').strip()
    description = (data.get('description') or '').strip()

    base_tables = current_app.config['BASE_TABLES']
    if not table_name:
        return jsonify({'error': 'table_name is required'}), 400
    if table_name in base_tables:
        return jsonify({'error': 'Table already exists'}), 400
    if not table_name.isidentifier():
        return jsonify({'error': 'Invalid table name'}), 400
    try:
        success = create_base_table(table_name, description, table_name)
    except Exception as exc:
        logger.exception('Failed to create table %s: %s', table_name, exc)
        return jsonify({'error': str(exc)}), 400
    if not success:
        return jsonify({'error': 'Failed to create table'}), 400

    reload_app_state()

    return jsonify({'success': True})
