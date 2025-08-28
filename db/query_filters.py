import logging
from db.database import SUPPORTS_REGEX
from db.schema import get_field_schema
from db.validation import validate_fields
from utils.field_registry import FIELD_TYPES

logger = logging.getLogger(__name__)


def _normalize_filter_values(value):
    """Return a list of non-empty filter values."""
    values = value if isinstance(value, list) else [value]
    return [v for v in values if v != ""]


def _operator_snippet(field: str, value: str, op: str, params: list[str]) -> str:
    """Build a SQL snippet for a single value based on the operator."""
    if op == "equals":
        params.append(value)
        return f"{field} = ?"
    if op == "starts_with":
        params.append(f"{value}%")
        return f"{field} LIKE ?"
    if op == "ends_with":
        params.append(f"%{value}")
        return f"{field} LIKE ?"
    if op == "not_contains":
        params.append(f"%{value}%")
        return f"{field} NOT LIKE ?"
    if op == "regex":
        if SUPPORTS_REGEX:
            params.append(value)
            return f"{field} REGEXP ?"
        params.append(f"%{value}%")
        return f"{field} LIKE ?"
    params.append(f"%{value}%")
    return f"{field} LIKE ?"


def _build_field_clause(
    field: str,
    values: list[str],
    op: str,
    mode: str,
    params: list[str],
) -> str | None:
    """Return a combined clause for all values of a field."""
    snippets = [_operator_snippet(field, v, op, params) for v in values]
    if not snippets:
        return None
    joiner = " AND " if mode == "all" else " OR "
    return "(" + joiner.join(snippets) + ")"


def _apply_date_ranges(
    date_starts: dict,
    date_ends: dict,
    clauses: list[str],
    params: list[str],
) -> None:
    """Append SQL clauses for collected date range filters."""
    for base in set(date_starts) | set(date_ends):
        start = date_starts.get(base)
        end = date_ends.get(base)
        if start and end:
            clauses.append(f"{base} BETWEEN ? AND ?")
            params.extend([start, end])
        elif start:
            clauses.append(f"{base} >= ?")
            params.append(start)
        elif end:
            clauses.append(f"{base} <= ?")
            params.append(end)


def _build_filters(
    table,
    search=None,
    filters=None,
    ops=None,
    modes=None,
):
    """Return SQL where clauses and params for the provided filters/search."""
    logger.debug(
        "Building filters table=%s search=%s filters=%s ops=%s modes=%s",
        table,
        search,
        filters,
        ops,
        modes,
        extra={"table": table, "search": search},
    )
    clauses: list[str] = []
    params: list[str] = []

    if filters:
        valid_keys = [
            f[:-4] if f.endswith("_min") or f.endswith("_max") else f[:-6] if f.endswith("_start") else f[:-4] if f.endswith("_end") else f
            for f in filters.keys()
        ]
        validate_fields(table, valid_keys)

        date_starts: dict = {}
        date_ends: dict = {}

        for fld, val in filters.items():
            clean_values = _normalize_filter_values(val)
            if not clean_values:
                continue
            if fld.endswith("_min"):
                base = fld[:-4]
                for v in clean_values:
                    clauses.append(f"{base} >= ?")
                    params.append(v)
            elif fld.endswith("_max"):
                base = fld[:-4]
                for v in clean_values:
                    clauses.append(f"{base} <= ?")
                    params.append(v)
            elif fld.endswith("_start"):
                base = fld[:-6]
                date_starts[base] = clean_values[0]
            elif fld.endswith("_end"):
                base = fld[:-4]
                date_ends[base] = clean_values[0]
            else:
                op = (ops or {}).get(fld, "contains")
                mode = (modes or {}).get(fld, "any")
                clause = _build_field_clause(fld, clean_values, op, mode, params)
                if clause:
                    clauses.append(clause)

        _apply_date_ranges(date_starts, date_ends, clauses, params)

    if search:
        search_term = search.strip()
        all_fields = get_field_schema()[table]
        search_fields = [
            f
            for f, m in all_fields.items()
            if m["type"] in FIELD_TYPES and FIELD_TYPES[m["type"]].searchable
        ]
        if search_fields:
            validate_fields(table, search_fields)
            subconds = [f"{f} LIKE ?" for f in search_fields]
            clauses.append("(" + " OR ".join(subconds) + ")")
            params.extend([f"%{search_term}%"] * len(subconds))

    logger.debug(
        "Built clauses=%s params=%s",
        clauses,
        params,
        extra={"table": table, "clauses": clauses},
    )
    return clauses, params
