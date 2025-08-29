import logging
from typing import Any, Iterable

from db.records import (
    get_record_by_id,
    update_field_value,
)
from db.edit_history import append_edit_log
from db.schema import get_field_schema
from utils.field_registry import get_field_type

logger = logging.getLogger(__name__)


def _normalize_value(ftype: str, value: Any) -> str:
    """Convert raw input into a normalized string for storage."""
    ft = get_field_type(ftype)
    if ft and ft.normalizer:
        return ft.normalizer(value)

    if ftype == "boolean":
        return "1" if str(value).lower() in {"1", "true", "on", "yes"} else "0"
    if ftype == "number":
        try:
            return str(float(value))
        except (TypeError, ValueError):
            logger.warning("Failed to normalize number", exc_info=True)
            return "0"
    if ftype in {"multi_select", "foreign_key"}:
        if isinstance(value, Iterable) and not isinstance(value, (str, bytes)):
            return ", ".join(str(v) for v in value)
        return "" if value is None else str(value)
    # Textarea sanitization happens in db layer
    return "" if value is None else str(value)


def update_record_field(table: str, record_id: int, field: str, value: Any) -> str:
    """Update a single record field and append to edit log."""
    schema = get_field_schema().get(table, {})
    fmeta = schema.get(field)
    if fmeta is None:
        raise ValueError("Unknown field")

    # Prevent edits to read-only fields
    if fmeta.get("readonly"):
        raise ValueError("Field is read-only")

    new_value = _normalize_value(fmeta["type"], value)

    prev_record = get_record_by_id(table, record_id)
    prev_value = prev_record.get(field) if prev_record else None

    success = update_field_value(table, record_id, field, new_value)
    if not success:
        raise RuntimeError("Database update failed")

    if prev_record is not None and str(prev_value) != str(new_value):
        append_edit_log(table, record_id, field, str(prev_value), str(new_value))

    logger.info(
        "Field updated for %s id=%s: %s -> %r",
        table,
        record_id,
        field,
        new_value,
        extra={
            "table": table,
            "record_id": record_id,
            "field": field,
            "new_value": new_value,
        },
    )
    return new_value


def bulk_update_records(table: str, ids: list[int], field: str, value: Any) -> int:
    """Update a field for many records, returning the count updated."""
    schema = get_field_schema().get(table, {})
    fmeta = schema.get(field)
    if fmeta is None:
        raise ValueError("Unknown field")

    new_value = _normalize_value(fmeta["type"], value)
    updated = 0
    for rid in ids:
        if update_field_value(table, rid, field, new_value):
            append_edit_log(table, rid, field, None, str(new_value))
            updated += 1
    logger.info(
        "Bulk updated %s records for %s.%s",
        updated,
        table,
        field,
        extra={"table": table, "field": field, "updated": updated},
    )
    return updated
