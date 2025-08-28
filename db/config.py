from datetime import datetime
from db.database import get_connection
import json
import logging

logger = logging.getLogger(__name__)


def get_config_rows(sections: str | list[str] | None = None):
    """Return configuration rows with metadata, optionally filtered by section."""

    query = (
        "SELECT key, value, section, type, description, "
        "date_updated, required, labels, options, wizard FROM config"
    )
    params: list[str] = []
    if sections:
        if isinstance(sections, str):
            sections = [sections]
        placeholders = ", ".join(["?"] * len(sections))
        query += f" WHERE section IN ({placeholders})"
        params = list(sections)

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()

    columns = [
        "key",
        "value",
        "section",
        "type",
        "description",
        "date_updated",
        "required",
        "labels",
        "options",
        "wizard",
    ]
    result = []
    for row in rows:
        item = dict(zip(columns, row))
        opts = item.get("options")
        if opts:
            try:
                item["options"] = json.loads(opts)
            except json.JSONDecodeError as exc:
                logger.exception(
                    "Invalid JSON in config options",
                    extra={"key": item.get("key"), "error": str(exc)},
                )
                item["options"] = []
        else:
            item["options"] = []
        result.append(item)

    return result


def get_layout_defaults() -> dict:
    """Return layout width/height defaults from the config table or registry."""
    from utils.field_registry import get_type_size_map

    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM config WHERE key = 'layout_defaults'")
        row = cur.fetchone()

    data = {}
    if row and row[0]:
        try:
            data = json.loads(row[0])
        except json.JSONDecodeError as exc:
            logger.exception(
                "Invalid JSON in layout_defaults config",
                extra={"key": "layout_defaults", "error": str(exc)},
            )
            data = {}

    if not data:
        size_map = get_type_size_map()
        data = {
            "width": {k: v[0] for k, v in size_map.items()},
            "height": {k: v[1] for k, v in size_map.items()},
        }

    return data


def get_relationship_visibility() -> dict:
    """Return per-table relationship visibility settings."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM config WHERE key = 'relationship_visibility'")
        row = cur.fetchone()
    if not row:
        return {}
    try:
        return json.loads(row[0])
    except json.JSONDecodeError as exc:
        logger.exception(
            "Invalid JSON in relationship_visibility config",
            extra={"key": "relationship_visibility", "error": str(exc)},
        )
        return {}


def update_relationship_visibility(table: str, visibility: dict) -> None:
    """Update visibility settings for a specific base table."""
    current = get_relationship_visibility()
    current[table] = visibility
    update_config("relationship_visibility", json.dumps(current))


def update_config(key: str, value: str) -> int:
    """Update a configuration value and timestamp."""

    with get_connection() as conn:
        cur = conn.cursor()
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            "UPDATE config SET value = ?, date_updated = ? WHERE key = ?",
            (value, timestamp, key),
        )
        if cur.rowcount == 0:
            cur.execute(
                "INSERT INTO config (key, value, date_updated) VALUES (?, ?, ?)",
                (key, value, timestamp),
            )
        conn.commit()
        affected = cur.rowcount

    if key == "db_path":
        # Refresh the global database path so subsequent connections
        # use the newly configured location.
        from db.database import init_db_path

        init_db_path(value)

    return affected

