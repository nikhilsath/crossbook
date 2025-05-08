import json
import re
import csv
from db.schema import get_field_schema

SCHEMA = get_field_schema()

def validation_sorter(table, field, header, fieldType, values):
    print("✅ Validation function was triggered.")
    if fieldType == "text":
        print("Text Validation Triggered")
        return validate_text_column(values)
    elif fieldType == "boolean":
        print("Boolean Validation Triggered")
        return validate_boolean_column(values)
    elif fieldType == "foreign_key":
        print("FK Validation Triggered")
        options = SCHEMA[table][field]["options"]
        return validate_select_column(values, options)
    elif fieldType == "multi_select":
        print("Multi Validation Triggered")
        options = SCHEMA[table][field]["options"]
        return validate_multi_select_column(values, options)
    elif fieldType == "number":
        print("Number Validation Triggered")
        return validate_number_column(values)
    elif fieldType == "select":
        print("Select Validation Triggered")
        options = SCHEMA[table][field]["options"]
        return validate_select_column(values, options)
    elif fieldType == "textarea":
        print("Textarea Validation Triggered")
        return validate_textarea_column(values)
    else:
        print("no validation for this datatype")


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
    for v in values:
        # Blank or whitespace-only
        if v is None or str(v).strip() == "":
            blank += 1
            continue

        s = str(v).strip()
        # Try to convert to number
        try:
            num = int(s) if integer_only else float(s)
        except ValueError:
            invalid += 1
            continue
        else:
            valid += 1

    return {
        "valid": valid,
        "invalid": invalid,
        "blank": blank
    }
def validate_boolean_column(values):
    valid = invalid = blank = 0
    for v in values:
        if not v or str(v).strip() == "":
            blank += 1
            continue
        s = str(v).strip().lower()
        if s in ("true", "false", "1", "0", "yes", "no"):
            valid += 1
        else:
            invalid += 1
    return {"valid": valid, "invalid": invalid, "blank": blank}
def validate_select_column(values: list[str], options: list[str]) -> dict:
    valid = invalid = blank = 0
    normalized_options = {opt.lower() for opt in options}
    for v in values:
        if not v or not str(v).strip():
            blank += 1
        elif str(v).strip().lower() in normalized_options:
            valid += 1
        else:
            invalid += 1
    return {"valid": valid, "invalid": invalid, "blank": blank}
def validate_multi_select_column(values: list[str], options: list[str]) -> dict:
    valid = invalid = blank = 0
    normalized_options = {opt.lower() for opt in options}

    for cell in values:
        cell_str = str(cell).strip()
        if not cell_str:
            blank += 1
            continue

        # Split on comma, then strip whitespace
        tags = [tag.strip() for tag in cell_str.split(',')]
        # Check every tag against allowed options
        if all(tag.lower() in normalized_options for tag in tags):
            valid += 1
        else:
            invalid += 1

    return {"valid": valid, "invalid": invalid, "blank": blank}
