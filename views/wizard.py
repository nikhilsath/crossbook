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
import logging
from utils.name_utils import to_identifier
import db.database as db_database
from db.bootstrap import initialize_database, ensure_default_configs
from db.config import update_config, get_config_rows
from db.schema import create_base_table
from db.edit_fields import add_column_to_table, add_field_to_schema
from imports.import_csv import parse_csv
from db.records import create_record
from views.admin import reload_app_state

wizard_bp = Blueprint('wizard', __name__)

logger = logging.getLogger(__name__)


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
    rows = []
    for r in get_config_rows():
        if r.get('wizard'):
            rows.append(r)
            continue
        if r.get('required'):
            val = r.get('value')
            if val is None or val == "":
                rows.append(r)
    for row in rows:
        if row['key'] == 'heading':
            row['labels'] = 'Main Heading'
    config = {row['key']: row['value'] for row in rows}
    config_display = config.copy()
    if 'filename' in config_display:
        import os
        config_display['filename'] = os.path.basename(config_display['filename'])
    logging_defaults = [r for r in rows if r['section'] == 'logging']
    other_defaults = [r for r in rows if r['section'] != 'logging']
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
                config=config_display,
                logging_defaults=logging_defaults,
                other_defaults=other_defaults,
                errors=errors,
            )
        for row in rows:
            val = request.form.get(row['key'])
            if val is not None:
                if row['key'] == 'filename':
                    import os
                    val = os.path.join('logs', os.path.basename(val))
                update_config(row['key'], val)
        progress['settings'] = True
        session['wizard_progress'] = progress
        return redirect(url_for('wizard.table_step'))
    return render_template(
        'wizard/wizard_settings.html',
        config=config_display,
        logging_defaults=logging_defaults,
        other_defaults=other_defaults,
        errors={},
    )


@wizard_bp.route('/wizard/table', methods=['GET', 'POST'])
def table_step():
    progress = session.setdefault('wizard_progress', {})
    error = None
    if request.method == 'POST':
        table_names = [to_identifier(t.strip(), 'tbl_') for t in request.form.getlist('table_name')]
        title_fields = [to_identifier(t.strip(), 'f_') for t in request.form.getlist('title_field')]
        descriptions = [d.strip() for d in request.form.getlist('description')]
        fields_json_list = request.form.getlist('fields_json')
        any_created = False

        for idx, table_name in enumerate(table_names):
            if not table_name:
                continue
            title_field = title_fields[idx] if idx < len(title_fields) else ''
            description = descriptions[idx] if idx < len(descriptions) else ''
            fields_json = fields_json_list[idx] if idx < len(fields_json_list) else ''

            if not title_field:
                error = 'Each table requires a title field.'
                continue

            if create_base_table(table_name, description, title_field):
                field_defs = []
                if fields_json:
                    try:
                        field_defs = json.loads(fields_json)
                    except Exception:
                        logger.exception('Failed to parse fields_json')

                for f in field_defs:
                    name = to_identifier(f.get('name'), 'f_')
                    if name == title_field:
                        continue
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
                        logger.exception('Failed to add field %s', name)
                any_created = True
            else:
                error = f'Table "{table_name}" could not be created.'

        if any_created:
            reload_app_state()
            progress['table'] = True
            session['wizard_progress'] = progress
            return redirect(url_for('wizard.import_step'))
        if not error:
            error = 'No tables were created. Please check the table names and title fields.'

    return render_template('wizard/wizard_table.html', error=error)


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
                    logger.exception('Failed to import row')
        progress['import'] = True
        session['wizard_progress'] = progress
        session['wizard_complete'] = True
        session.pop('wizard_progress', None)
        return redirect(url_for('home'))
    return render_template('wizard/wizard_import.html', base_tables=base_tables)
