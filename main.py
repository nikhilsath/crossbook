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
from db.bootstrap import initialize_database
from db.schema import (
    get_field_schema,
    update_foreign_field_options,
    load_base_tables,
    load_card_info,
)
from db.config import get_all_config
from utils.flask_helpers import start_timer, log_request, log_exception
from utils.field_registry import FIELD_TYPES

app = Flask(__name__, static_url_path='/static')
app.secret_key = os.environ.get('SECRET_KEY', 'crossbook-secret')
app.jinja_env.add_extension('jinja2.ext.do')

init_db_path()

needs_init = False
status = check_db_status(DB_PATH)
if status == 'missing':
    needs_init = True
else:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='config'"
            )
            if cur.fetchone() is None:
                needs_init = True
    except Exception:
        needs_init = True

if needs_init:
    initialize_database(DB_PATH)

with get_connection() as conn:
    app.config['CARD_INFO'] = load_card_info(conn)
    app.config['BASE_TABLES'] = load_base_tables(conn)

configure_logging(app)

werk_logger = logging.getLogger("werkzeug")
werk_logger.disabled = True

app.before_request(start_timer)

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
    return {
        'field_schema': get_field_schema(),
        'update_foreign_field_options': update_foreign_field_options,
        'nav_cards': current_app.config['CARD_INFO'],
        'base_tables': current_app.config['BASE_TABLES'],
        'field_macro_map': {name: ft.macro for name, ft in FIELD_TYPES.items() if ft.macro},
    }

@app.route("/")
def home():
    heading = get_all_config().get('heading', 'Load the Glass Cannon')
    return render_template(
        "index.html",
        cards=current_app.config['CARD_INFO'],
        heading=heading,
    )

if __name__ == "__main__":
    update_foreign_field_options()
    app.run(debug=True)
