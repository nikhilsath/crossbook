import os
import json
from huey import SqliteHuey
from db.database import get_connection
from db.records import create_record

# Huey queue for background imports
huey = SqliteHuey(
    'crossbook-tasks',  # queue name
    filename=os.path.join(os.getcwd(), 'data', 'huey.db'),
    store_none=False,  # don't clutter the DB with None results
)


def init_import_table():
    """Ensure the import_status table exists."""
    with get_connection() as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS import_status (\n"
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "  status TEXT,\n"
            "  total_rows INTEGER,\n"
            "  imported_rows INTEGER,\n"
            "  errors TEXT\n"
            ")"
        )
        conn.commit()


def _update_import_status(job_id, **kwargs):
    """Update fields for a given import job."""
    if not kwargs:
        return
    fields = ", ".join(f"{k} = ?" for k in kwargs)
    params = list(kwargs.values()) + [job_id]
    with get_connection() as conn:
        conn.execute(f"UPDATE import_status SET {fields} WHERE id = ?", params)
        conn.commit()


def _run_import(job_id, table, rows):
    """Helper to perform the actual row import."""
    _update_import_status(job_id, status="in_progress", total_rows=len(rows))
    errors: list[dict] = []
    for idx, row in enumerate(rows, start=1):
        try:
            if create_record(table, row) is None:
                raise Exception("Failed to create")
        except Exception as exc:  # noqa: BLE001
            errors.append({"row": idx, "message": str(exc)})
        if idx % 10 == 0 or idx == len(rows):
            _update_import_status(job_id, imported_rows=idx, errors=json.dumps(errors))
    _update_import_status(job_id, status="complete")
    return {"job_id": job_id, "imported": len(rows) - len(errors), "errors": errors}


@huey.task()
def process_import(job_id, table, rows):
    """Background task to create records from parsed CSV rows."""
    return _run_import(job_id, table, rows)


@huey.task()
def import_rows(table, rows):
    """Create a new import job and process the provided rows."""
    init_import_table()
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO import_status (status, total_rows, imported_rows, errors) VALUES (?, ?, ?, ?)",
            ("queued", len(rows), 0, "[]"),
        )
        job_id = cur.lastrowid
        conn.commit()
    return _run_import(job_id, table, rows)

