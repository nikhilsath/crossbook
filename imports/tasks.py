import os
import json
import logging
import sqlite3
from huey import SqliteHuey
from db.database import get_connection
from db.records import create_record

# Project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

logger = logging.getLogger(__name__)

# Huey queue for background imports
huey = SqliteHuey(
    'crossbook-tasks',  # queue name
    filename=os.path.join(PROJECT_ROOT, 'data', 'huey.db'),
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
    logger.info(
        "Import job %s started for table %s",
        job_id,
        table,
        extra={"job_id": job_id, "table": table},
    )
    _update_import_status(job_id, status="in_progress", total_rows=len(rows))
    errors: list[dict] = []
    try:
        for idx, row in enumerate(rows, start=1):
            try:
                if create_record(table, row) is None:
                    raise sqlite3.DatabaseError("Failed to create")
            except (sqlite3.DatabaseError, ValueError) as exc:  # noqa: BLE001
                logger.exception(
                    "Failed to import row",  # noqa: TRY401
                    extra={"job_id": job_id, "table": table, "row": idx},
                )
                errors.append({"row": idx, "message": str(exc)})
            if idx % 10 == 0 or idx == len(rows):
                logger.info(
                    "Job %s table %s processed %s/%s rows",
                    job_id,
                    table,
                    idx,
                    len(rows),
                    extra={
                        "job_id": job_id,
                        "table": table,
                        "processed": idx,
                        "total_rows": len(rows),
                    },
                )
                _update_import_status(
                    job_id, imported_rows=idx, errors=json.dumps(errors)
                )
        _update_import_status(job_id, status="complete")
        # trigger automation rules that run on import
        from automation import engine as automation_engine
        automation_engine.run_import_rules(table)
        logger.info(
            "Import job %s for table %s complete: %s rows imported, %s errors",
            job_id,
            table,
            len(rows) - len(errors),
            len(errors),
            extra={
                "job_id": job_id,
                "table": table,
                "imported": len(rows) - len(errors),
                "error_count": len(errors),
            },
        )
        return {"job_id": job_id, "imported": len(rows) - len(errors), "errors": errors}
    except sqlite3.DatabaseError:
        logger.exception(
            "Import job %s for table %s failed",
            job_id,
            table,
            extra={"job_id": job_id, "table": table},
        )
        _update_import_status(job_id, status="failed")
        raise
    except Exception:
        logger.exception(
            "Import job %s for table %s failed",
            job_id,
            table,
            extra={"job_id": job_id, "table": table},
        )
        _update_import_status(job_id, status="failed")
        raise


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

