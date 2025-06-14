from flask import Flask, render_template, current_app, redirect, url_for, session, request
import logging
import sqlite3
import os
from logging_setup import configure_logging
from db.database import (
    get_connection,
    init_db_path,
    check_db_status,
    DB_PATH,
)

from db.schema import (
    get_field_schema,
    update_foreign_field_options,
    load_base_tables,
    load_card_info,
)
from db.config import get_config_rows
from utils.flask_helpers import start_timer, log_request, log_exception
from utils.field_registry import FIELD_TYPES

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'crossbook-secret')
app.jinja_env.add_extension('jinja2.ext.do')

init_db_path()

needs_wizard = False
status = check_db_status(DB_PATH)
if status == 'valid':
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='config'"
            )
            if cur.fetchone() is None:
                needs_wizard = True
            else:
                from db.config import get_config_rows

                rows = get_config_rows('database')
                cfg = {row['key']: row['value'] for row in rows}
                cfg_path = cfg.get('db_path')
                if cfg_path:
                    init_db_path(cfg_path)
    except Exception:
        needs_wizard = True
else:
    needs_wizard = True

app.config['NEEDS_WIZARD'] = needs_wizard

if not needs_wizard:
    with get_connection() as conn:
        app.config['CARD_INFO'] = load_card_info(conn)
        app.config['BASE_TABLES'] = load_base_tables(conn)
else:
    app.config['CARD_INFO'] = []
    app.config['BASE_TABLES'] = []

configure_logging(app)

werk_logger = logging.getLogger("werkzeug")
werk_logger.disabled = True

app.before_request(start_timer)

@app.before_request
def wizard_redirect():
    if current_app.config.get('NEEDS_WIZARD') and not request.path.startswith('/wizard'):
        return redirect(url_for('wizard.wizard_start'))

app.after_request(log_request)
app.teardown_request(log_exception)

from views.admin import admin_bp
from views.records import records_bp
from views.wizard import wizard_bp
app.register_blueprint(admin_bp)
app.register_blueprint(records_bp)
app.register_blueprint(wizard_bp)

@app.context_processor
def inject_field_schema():
    schema = get_field_schema()
    current_app.logger.debug("Injected field schema keys: %s", list(schema.keys()))
    return {
        'field_schema': schema,
        'update_foreign_field_options': update_foreign_field_options,
        'nav_cards': current_app.config['CARD_INFO'],
        'base_tables': current_app.config['BASE_TABLES'],
        'field_macro_map': {name: ft.macro for name, ft in FIELD_TYPES.items() if ft.macro},
    }

@app.route("/")
def home():
    rows = get_config_rows()
    cfg = {row['key']: row['value'] for row in rows}
    heading = cfg.get('heading')
    return render_template(
        "index.html",
        cards=current_app.config['CARD_INFO'],
        heading=heading,
    )

if __name__ == "__main__":
    update_foreign_field_options()
    app.run(debug=True)
