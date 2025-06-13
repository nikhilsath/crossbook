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
from db.database import DB_PATH, check_db_status, init_db_path
from db.bootstrap import initialize_database
from db.config import update_config, get_all_config
from db.schema import create_base_table, refresh_card_cache
from db.edit_fields import add_column_to_table, add_field_to_schema
from imports.import_csv import parse_csv
from db.records import create_record
from views.admin import write_local_settings

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
                init_db_path(save_path)
                update_config('db_path', save_path)
                write_local_settings(save_path)
        name = request.form.get('create_name')
        if name:
            filename = secure_filename(name)
            if not filename.endswith('.db'):
                filename += '.db'
            save_path = os.path.join('data', filename)
            open(save_path, 'a').close()
            initialize_database(save_path)
            init_db_path(save_path)
            update_config('db_path', save_path)
            write_local_settings(save_path)
        progress['database'] = True
        session['wizard_progress'] = progress
        return redirect(url_for('wizard.settings_step'))
    status = check_db_status(DB_PATH)
    return render_template('wizard_database.html', db_path=DB_PATH, db_status=status)


@wizard_bp.route('/wizard/settings', methods=['GET', 'POST'])
def settings_step():
    progress = session.setdefault('wizard_progress', {})
    config = get_all_config()
    if request.method == 'POST':
        heading = request.form.get('heading')
        level = request.form.get('log_level')
        if heading is not None:
            update_config('heading', heading)
        if level is not None:
            update_config('log_level', level)
        progress['settings'] = True
        session['wizard_progress'] = progress
        return redirect(url_for('wizard.table_step'))
    return render_template('wizard_settings.html', config=config)


@wizard_bp.route('/wizard/table', methods=['GET', 'POST'])
def table_step():
    progress = session.setdefault('wizard_progress', {})
    if request.method == 'POST':
        table_name = (request.form.get('table_name') or '').strip()
        description = (request.form.get('description') or '').strip()
        fields_json = request.form.get('fields_json', '')
        fields_text = request.form.get('fields', '')
        if table_name:
            if create_base_table(table_name, description):
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
                card_info, base_tables = refresh_card_cache()
                current_app.config['CARD_INFO'] = card_info
                current_app.config['BASE_TABLES'] = base_tables
                progress['table'] = True
                session['wizard_progress'] = progress
                return redirect(url_for('wizard.import_step'))
    return render_template('wizard_table.html')


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
    return render_template('wizard_import.html', base_tables=base_tables)
