from flask import Flask, render_template, current_app
import logging
from logging_setup import configure_logging
from db.database import get_connection
from db.schema import (
    get_field_schema,
    update_foreign_field_options,
    load_base_tables,
    load_card_info,
)
from db.config import get_all_config
from utils.flask_helpers import start_timer, log_request, log_exception

app = Flask(__name__, static_url_path='/static')
app.jinja_env.add_extension('jinja2.ext.do')

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
app.register_blueprint(admin_bp)
app.register_blueprint(records_bp)

@app.context_processor
def inject_field_schema():
    return {
        'field_schema': get_field_schema(),
        'update_foreign_field_options': update_foreign_field_options,
        'nav_cards': current_app.config['CARD_INFO'],
        'base_tables': current_app.config['BASE_TABLES'],
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
