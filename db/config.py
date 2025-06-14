from datetime import datetime
from db.database import get_connection
import json


def get_config_rows(sections: str | list[str] | None = None):
    """Return configuration rows with metadata, optionally filtered by section."""

    query = (
        "SELECT key, value, section, type, description, "
        "date_updated, required, labels, options FROM config"
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
    ]
    result = []
    for row in rows:
        item = dict(zip(columns, row))
        opts = item.get("options")
        if opts:
            try:
                item["options"] = json.loads(opts)
            except Exception:
                item["options"] = []
        else:
            item["options"] = []
        result.append(item)

    return result


def get_layout_defaults() -> dict:
    """Return layout width/height defaults from the config table."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT value FROM config WHERE key = 'layout_defaults'")
        row = cur.fetchone()

    if not row:
        return {}
    try:
        return json.loads(row[0])
    except Exception:
        return {}


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

