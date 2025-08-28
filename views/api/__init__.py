import logging
from flask import Blueprint, jsonify
from db.database import get_connection
from db.schema import load_card_info

api_bp = Blueprint('api', __name__)

logger = logging.getLogger(__name__)

@api_bp.route('/api/base-tables')
def api_base_tables():
    """Return configured base tables with display info."""
    with get_connection() as conn:
        data = load_card_info(conn)
    logger.debug(
        "Loaded %d base tables",
        len(data),
        extra={"base_table_count": len(data)},
    )
    return jsonify(data)

