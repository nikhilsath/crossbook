"""Validation orchestration and field type registration.

Column validators live in :mod:`utils.validators`.
Value normalizers live in :mod:`utils.normalizers`.
This module wires them together into the field type registry and exposes the
:func:`validation_sorter` dispatcher used by views.
"""

import logging
from db.schema import get_field_schema
from utils.field_registry import register_type, get_field_type
from utils.validators import (
    validate_text_column,
    validate_textarea_column,
    validate_number_column,
    validate_boolean_column,
    validate_select_column,
    validate_multi_select_column,
)
from utils.normalizers import normalize_boolean, normalize_number, normalize_multi

logger = logging.getLogger(__name__)


def get_options(table: str, field: str) -> list[str]:
    """Return options for the given field from the field schema."""
    schema = get_field_schema()
    return schema.get(table, {}).get(field, {}).get("options", [])


def validation_sorter(table, field, header, fieldType, values):
    logger.debug(
        "✅ Validation function was triggered.",
        extra={"table": table, "field": field},
    )

    ft = get_field_type(fieldType)
    if not ft or not ft.validator:
        logger.debug(
            "no validation for this datatype",
            extra={"datatype": fieldType},
        )
        return {}

    result = ft.validator(table, field, values)

    classes = []
    if result.get("blank", 0) > 0:
        classes.append("matched-blank")
    if result.get("valid", 0) > 0:
        classes.append("matched-valid")
    if result.get("warning", 0) > 0:
        classes.append("matched-warnings")
    if result.get("invalid", 0) > 0:
        classes.append("matched-invalid")
    if classes:
        # Join into a space-delimited string so JS .classList.add() can apply all
        result["cssClass"] = " ".join(classes)

    return result


# Register built-in field types with the registry
register_type(
    'text',
    sql_type='TEXT',
    validator=lambda t, f, v: validate_text_column(v),
    default_width=12,
    default_height=4,
    macro='render_text',
    filter_macro='text_filter',
    searchable=True,
)
register_type(
    'number',
    sql_type='REAL',
    validator=lambda t, f, v: validate_number_column(v),
    default_width=4,
    default_height=3,
    macro='render_number',
    filter_macro='number_filter',
    normalizer=normalize_number,
    numeric=True,
)
register_type(
    'date',
    sql_type='TEXT',
    validator=lambda t, f, v: validate_text_column(v),
    default_width=6,
    default_height=4,
    macro='render_date',
    filter_macro='date_filter',
)
register_type(
    'select',
    sql_type='TEXT',
    validator=lambda t, f, v: validate_select_column(v, get_options(t, f)),
    default_width=5,
    default_height=4,
    macro='render_select',
    filter_macro='select_filter',
    allows_options=True,
    searchable=True,
)
register_type(
    'multi_select',
    sql_type='TEXT',
    validator=lambda t, f, v: validate_multi_select_column(v, get_options(t, f)),
    default_width=6,
    default_height=8,
    macro='render_multi_select',
    filter_macro='multi_select_popover',
    normalizer=normalize_multi,
    allows_options=True,
    allows_multiple=True,
    searchable=True,
)
register_type(
    'foreign_key',
    sql_type='TEXT',
    validator=lambda t, f, v: validate_select_column(v, get_options(t, f)),
    default_width=5,
    default_height=10,
    macro='render_foreign_key',
    filter_macro='multi_select_popover',
    normalizer=normalize_multi,
    allows_foreign_key=True,
    allows_multiple=True,
)
register_type(
    'boolean',
    sql_type='INTEGER',
    validator=lambda t, f, v: validate_boolean_column(v),
    default_width=3,
    default_height=7,
    macro='render_boolean',
    filter_macro='boolean_filter',
    normalizer=normalize_boolean,
    is_boolean=True,
)
register_type(
    'textarea',
    sql_type='TEXT',
    validator=lambda t, f, v: validate_textarea_column(v),
    default_width=12,
    default_height=18,
    macro='render_textarea',
    filter_macro='text_filter',
    searchable=True,
    is_textarea=True,
)
register_type(
    'url',
    sql_type='TEXT',
    validator=lambda t, f, v: validate_text_column(v),
    default_width=12,
    default_height=4,
    macro='render_url',
    filter_macro='text_filter',
    searchable=True,
    is_url=True,
)
