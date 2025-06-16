from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    current_app,
)
from werkzeug.utils import secure_filename
import os
import json
import db.database as db_database
from db.bootstrap import initialize_database, ensure_default_configs
from db.config import update_config, get_config_rows
from db.schema import create_base_table
from db.edit_fields import add_column_to_table, add_field_to_schema
from imports.import_csv import parse_csv
from db.records import create_record
from views.admin import reload_app_state

wizard_bp = Blueprint('wizard', __name__)


def _next_step():
    progress = session.get('wizard_progress', {})
    if not progress.get('database'):
        return 'wizard.database_step'
    if not progress.get('settings'):
        return 'wizard.settings_step'
    if not progress.get('table'):
        return 'wizard.table_step'
    if not progress.get('skip_import') and not progress.get('import'):
        return 'wizard.import_step'
    return None


@wizard_bp.route('/wizard/')
def wizard_start():
    progress = session.get('wizard_progress')
    if not progress:
        return redirect(url_for('home'))
    next_ep = _next_step()
    if next_ep:
        return redirect(url_for(next_ep))
    session['wizard_complete'] = True
    session.pop('wizard_progress', None)
    return redirect(url_for('home'))


@wizard_bp.route('/wizard/skip-import')
def skip_import():
    progress = session.setdefault('wizard_progress', {})
    progress['skip_import'] = True
    session['wizard_progress'] = progress
    return redirect(url_for('wizard.wizard_start'))


@wizard_bp.route('/wizard/database', methods=['GET', 'POST'])
def database_step():
    progress = session.setdefault('wizard_progress', {})
    if request.method == 'POST':
        if 'file' in request.files and request.files['file'].filename:
            file = request.files['file']
            filename = secure_filename(file.filename)
            if filename.endswith('.db'):
                save_path = os.path.join('data', filename)
                file.save(save_path)
                initialize_database(save_path)
                ensure_default_configs(save_path)
                db_database.init_db_path(save_path)
                update_config('db_path', save_path)
                reload_app_state()
        name = request.form.get('create_name')
        if name:
            filename = secure_filename(name)
            if not filename.endswith('.db'):
                filename += '.db'
            save_path = os.path.join('data', filename)
            open(save_path, 'a').close()
            initialize_database(save_path)
            ensure_default_configs(save_path)
            db_database.init_db_path(save_path)
            update_config('db_path', save_path)
            reload_app_state()
        progress['database'] = True
        session['wizard_progress'] = progress
        return redirect(url_for('wizard.settings_step'))
    status = db_database.check_db_status(db_database.DB_PATH)
    return render_template('wizard/wizard_database.html', db_path=db_database.DB_PATH, db_status=status)


@wizard_bp.route('/wizard/settings', methods=['GET', 'POST'])
def settings_step():
    progress = session.setdefault('wizard_progress', {})
    rows = get_config_rows()
    for row in rows:
        try:
            row['options'] = json.loads(row.get('options') or '[]')
        except Exception:
            row['options'] = []
    config = {row['key']: row['value'] for row in rows}
    if request.method == 'POST':
        handler_type = request.form.get('handler_type', config.get('handler_type'))
        errors = {}
        for row in rows:
            key = row['key']
            val = request.form.get(key)
            if row.get('required') and not val:
                errors[key] = True
        if handler_type == 'rotating':
            for key in ('max_file_size', 'backup_count'):
                if not request.form.get(key):
                    errors[key] = True
        elif handler_type == 'timed':
            for key in ('backup_count', 'when_interval', 'interval_count'):
                if not request.form.get(key):
                    errors[key] = True
        if errors:
            return render_template(
                'wizard/wizard_settings.html',
                config=config,
                defaults=rows,
                errors=errors,
            )
        for row in rows:
            val = request.form.get(row['key'])
            if val is not None:
                update_config(row['key'], val)
        progress['settings'] = True
        session['wizard_progress'] = progress
        return redirect(url_for('wizard.table_step'))
    return render_template('wizard/wizard_settings.html', config=config, defaults=rows, errors={})


@wizard_bp.route('/wizard/table', methods=['GET', 'POST'])
def table_step():
    progress = session.setdefault('wizard_progress', {})
    if request.method == 'POST':
        table_name = (request.form.get('table_name') or '').strip()
        title_field = (request.form.get('title_field') or '').strip()
        description = (request.form.get('description') or '').strip()
        fields_json = request.form.get('fields_json', '')
        fields_text = request.form.get('fields', '')
        if table_name and title_field:
            if create_base_table(table_name, description, title_field):
                field_defs = []
                if fields_json:
                    try:
                        field_defs = json.loads(fields_json)
                    except Exception:
                        current_app.logger.exception('Failed to parse fields_json')
                else:
                    for line in fields_text.splitlines():
                        if ':' in line:
                            name, ftype = [p.strip() for p in line.split(':', 1)]
                            if name:
                                field_defs.append({'name': name, 'type': ftype})

                for f in field_defs:
                    if f.get('name') == title_field:
                        continue
                    name = f.get('name')
                    ftype = f.get('type')
                    if not name or not ftype:
                        continue
                    try:
                        add_column_to_table(table_name, name, ftype)
                        add_field_to_schema(
                            table_name,
                            name,
                            ftype,
                            f.get('options'),
                            f.get('foreign_key'),
                        )
                    except Exception:
                        current_app.logger.exception('Failed to add field %s', name)
                reload_app_state()
                progress['table'] = True
                session['wizard_progress'] = progress
                return redirect(url_for('wizard.import_step'))
    return render_template('wizard/wizard_table.html')


@wizard_bp.route('/wizard/import', methods=['GET', 'POST'])
def import_step():
    progress = session.setdefault('wizard_progress', {})
    if progress.get('skip_import'):
        progress['import'] = True
        session['wizard_progress'] = progress
        session['wizard_complete'] = True
        session.pop('wizard_progress', None)
        return redirect(url_for('home'))

    base_tables = current_app.config.get('BASE_TABLES', [])
    if request.method == 'POST':
        table = request.form.get('table')
        file = request.files.get('file')
        if table and file and file.filename.endswith('.csv'):
            headers, rows = parse_csv(file)
            for row in rows:
                try:
                    create_record(table, row)
                except Exception:
                    current_app.logger.exception('Failed to import row')
        progress['import'] = True
        session['wizard_progress'] = progress
        session['wizard_complete'] = True
        session.pop('wizard_progress', None)
        return redirect(url_for('home'))
    return render_template('wizard/wizard_import.html', base_tables=base_tables)
