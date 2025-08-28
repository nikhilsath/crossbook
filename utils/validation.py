import re
import csv
import logging
from db.schema import get_field_schema
from utils.field_registry import register_type, get_field_type

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
        


def validate_text_column(values):
    valid = invalid = blank = warning = 0
    details = {"blank": [],"invalid":[],"warning":[],"valid":[]}
    for idx, v in enumerate(values, start=1):
        if not v or v.strip() == "":
            blank += 1
            details["blank"].append(idx)
            continue
        if len(v) > 1000:
            invalid += 1
            details["invalid"].append({"row": idx, "reason": "length exceeds 1000 characters"})
        else:
            valid += 1
            details["valid"].append(idx)
        # warning check based on common identifiers 
        if any([
            re.search(r"\{.*?\}", v),                 # JSON
            re.search(r"<[a-z][\s\S]*?>", v),         # HTML tags
            re.search(r"#+\s", v)                     # markdown headers
        ]):
            warning += 1
            details["warning"].append({"row": idx, "reason": "contains JSON,HTML, or MD"})
    return {
        "valid": valid,
        "invalid": invalid,
        "blank": blank,
        "warning": warning,
        "details": details
    }
def validate_textarea_column(values):
    max_size = csv.field_size_limit()  # default ~131072 bytes
    details = {"blank": [],"invalid":[],"warning":[],"valid":[]}
    valid = invalid = blank = warning = 0
    for idx, v in enumerate(values, start=1):
        if not v or v.strip() == "":
            blank += 1
            details["blank"].append(idx)
            continue
        # Invalid if over CSV field limit
        if len(v) > max_size:
            invalid += 1
            details["invalid"].append({"row": idx, "reason": f"length exceeds {max_size} characters"})
        else:
            valid += 1
            details["valid"].append(idx)
        # Warning: JSON-like content
        if re.search(r"\{.*?\}", v):
            warning += 1
            details["warning"].append({"row": idx, "reason": "Possibly contains JSON"})
    return {
        "valid": valid,
        "invalid": invalid,
        "blank": blank,
        "warning": warning,
        "details": details
    }
def validate_number_column(values, integer_only=False):
    valid = invalid = blank = 0
    details = {"blank": [],"invalid":[],"warning":[],"valid":[]}
    for idx, v in enumerate(values, start=1):
        if not v or v.strip() == "":
            blank += 1
            details["blank"].append(idx)
            continue
        s = str(v).strip()
        # Try to convert to number
        try:
            int(s) if integer_only else float(s)
        except ValueError:
            invalid += 1
            details["invalid"].append({"row": idx, "reason": "not a number", })
            continue
        else:
            valid += 1
            details["valid"].append(idx)
    return {
        "valid": valid,
        "invalid": invalid,
        "blank": blank,
        "details": details
    }
def validate_boolean_column(values):
    valid = invalid = blank = 0
    details = {"blank": [],"invalid":[],"warning":[],"valid":[]}
    for idx, v in enumerate(values, start=1):
        if not v or v.strip() == "":
            blank += 1
            details["blank"].append(idx)
            continue
        s = str(v).strip().lower()
        if s in ("true", "false", "1", "0", "yes", "no"):
            valid += 1
            details["valid"].append(idx)
        else:
            invalid += 1
            details["invalid"].append({"row": idx, "reason": "invalid boolean value","value":v })
    return {"valid": valid, "invalid": invalid, "blank": blank, "details":details}
def validate_select_column(values: list[str], options: list[str]) -> dict:
    valid = invalid = blank = 0
    normalized_options = {opt.lower() for opt in options}
    details = {"blank": [],"invalid":[],"warning":[],"valid":[]}
    for idx, v in enumerate(values, start=1):
        if not v or v.strip() == "":
            blank += 1
            details["blank"].append(idx)
        elif str(v).strip().lower() in normalized_options:
            valid += 1
            details["valid"].append(idx)
        else:
            invalid += 1
            details["invalid"].append({"row": idx, "reason": "does not match available options","value":v })
    return {"valid": valid, "invalid": invalid, "blank": blank, "details":details}
def validate_multi_select_column(values: list[str], options: list[str]) -> dict:
    valid = invalid = blank = warning = 0
    details = {"valid": [],"invalid": [],"blank": [],"warning": []}
    # Prepare lookup
    normalized_options = {opt.lower() for opt in options}
    for idx, raw in enumerate(values, start=1):
        cell = str(raw).strip()
        # Blank cell
        if not cell:
            blank += 1
            details["blank"].append(idx)
            continue
        # Split into individual tags
        tags = [t.strip() for t in cell.split(',')]
        # Identify any tags not in the allowed list
        invalid_tags = [t for t in tags if t.lower() not in normalized_options]
        if not invalid_tags:
            valid += 1
            details["valid"].append(idx)
        else:
            invalid += 1
            details["invalid"].append({
                "row": idx,
                "value": raw,
                "reason": f"invalid tags: {invalid_tags}"
            })

    return {
        "valid": valid,
        "invalid": invalid,
        "blank": blank,
        "warning": warning,
        "details": details
    }


def normalize_boolean(value):
    return "1" if str(value).lower() in {"1", "true", "on", "yes"} else "0"


def normalize_number(value):
    try:
        return str(float(value))
    except (TypeError, ValueError):
        return "0"


def normalize_multi(value):
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(v) for v in value)
    return "" if value is None else str(value)

# Register built-in field types with the registry
register_type(
    'title',
    sql_type='TEXT',
    validator=lambda t, f, v: validate_text_column(v),
    default_width=12,
    default_height=4,
    macro='render_text',
    filter_macro='text_filter',
    searchable=True,
)
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
