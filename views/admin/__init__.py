from flask import Blueprint, render_template, redirect, url_for, current_app
import logging
from db.schema import refresh_card_cache, update_foreign_field_options
from db.config import get_config_rows
from db.database import init_db_path, check_db_status, DB_PATH
import sqlite3

admin_bp = Blueprint('admin', __name__)

logger = logging.getLogger(__name__)


def reload_app_state() -> None:
    """Refresh cached navigation and schema data after a DB change."""
    logger.info(
        "Reloading application state",
        extra={"action": "reload_app_state"},
    )
    try:
        rows = get_config_rows('database')
        cfg = {row['key']: row['value'] for row in rows}
        init_db_path(cfg.get('db_path'))
    except sqlite3.DatabaseError:
        logger.exception("Failed to load database configuration")
        init_db_path()

    card_info, base_tables = refresh_card_cache()
    current_app.config['CARD_INFO'] = card_info
    current_app.config['BASE_TABLES'] = base_tables
    update_foreign_field_options()
    current_app.jinja_env.cache.clear()

    # Update wizard state based on new database status
    status = check_db_status(DB_PATH)
    current_app.config['NEEDS_WIZARD'] = status != 'valid'
    logger.debug(
        "App state reloaded with %d base tables",
        len(base_tables),
        extra={"base_table_count": len(base_tables)},
    )


@admin_bp.route('/admin')
def admin_page():
    return render_template('admin/admin.html')


@admin_bp.route('/admin/users')
def admin_users():
    return render_template('admin/admin_users.html')


@admin_bp.route('/admin/automation')
def admin_automation():
    return render_template('admin/admin_automation.html')


@admin_bp.route('/admin.html')
def admin_html_redirect():
    return redirect(url_for('admin.admin_page'))


from . import dashboard  # noqa: F401  # register routes
from . import config  # noqa: F401  # register routes
from . import imports  # noqa: F401  # register routes
from . import automation  # noqa: F401  # register routes
from . import fields  # noqa: F401  # register routes

__all__ = [
    'admin_bp',
    'reload_app_state',
]
