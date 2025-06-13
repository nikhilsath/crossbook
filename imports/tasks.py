import os
import json
from huey import SqliteHuey
from db.database import get_connection
from db.records import create_record

# Huey queue for background imports
huey = SqliteHuey(
    'crossbook-tasks',                         # queue name
    filename=os.path.join(os.getcwd(),         # ensure this points to your data/ folder
                          'data',
                          'huey.db'),
    store_none=False                            # don’t clutter the DB with None results
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


@huey.task()
def process_import(job_id, table, rows):
    """Background task to create records from parsed CSV rows."""
    _update_import_status(job_id, status="in_progress", total_rows=len(rows))
    errors = []
    for idx, row in enumerate(rows, start=1):
        if create_record(table, row) is None:
            errors.append({"row": idx, "message": "Failed to create"})
        _update_import_status(job_id, imported_rows=idx, errors=json.dumps(errors))
    _update_import_status(job_id, status="complete")
    return {"imported": len(rows) - len(errors), "errors": errors}

