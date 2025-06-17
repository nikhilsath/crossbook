from flask import Blueprint, render_template, redirect, url_for, current_app
import logging
from db.schema import refresh_card_cache, update_foreign_field_options

admin_bp = Blueprint('admin', __name__)

logger = logging.getLogger(__name__)


def reload_app_state() -> None:
    """Refresh cached navigation and schema data after a DB change."""
    card_info, base_tables = refresh_card_cache()
    current_app.config['CARD_INFO'] = card_info
    current_app.config['BASE_TABLES'] = base_tables
    update_foreign_field_options()
    current_app.jinja_env.cache.clear()


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

__all__ = [
    'admin_bp',
    'reload_app_state',
]
