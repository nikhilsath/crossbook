import re
import csv
import logging
from db.schema import get_field_schema

logger = logging.getLogger(__name__)
SCHEMA = get_field_schema()

# Map field types to a tuple of (log message, validator function)
VALIDATION_DISPATCH = {
    "text": ("Text Validation Triggered", lambda table, field, values: validate_text_column(values)),
    "boolean": ("Boolean Validation Triggered", lambda table, field, values: validate_boolean_column(values)),
    "foreign_key": (
        "FK Validation Triggered",
        lambda table, field, values: validate_select_column(values, SCHEMA[table][field]["options"]),
    ),
    "url": ("URL Validation Triggered", lambda table, field, values: validate_text_column(values)),
    "multi_select": (
        "Multi Validation Triggered",
        lambda table, field, values: validate_multi_select_column(values, SCHEMA[table][field]["options"]),
    ),
    "number": ("Number Validation Triggered", lambda table, field, values: validate_number_column(values)),
    "select": (
        "Select Validation Triggered",
        lambda table, field, values: validate_select_column(values, SCHEMA[table][field]["options"]),
    ),
    "textarea": ("Textarea Validation Triggered", lambda table, field, values: validate_textarea_column(values)),
}

def validation_sorter(table, field, header, fieldType, values):
    logger.debug("✅ Validation function was triggered.")

    # Lookup validator and log message from dispatch table
    dispatch_entry = VALIDATION_DISPATCH.get(fieldType)
    if not dispatch_entry:
        logger.debug("no validation for this datatype")
        return {}

    log_msg, validator = dispatch_entry
    logger.debug(log_msg)
    result = validator(table, field, values)

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
            details["invalid"].append({"row": idx, "reason": "length exceeds 1000 characters"})
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
