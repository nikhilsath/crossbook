import json
import re
import csv

def validation_sorter(table, field, header, fieldType, values):
    print("✅ Validation function was triggered.")
    if fieldType == "text":
        print("Text Validation Triggered")
        validate_text_column(values)
        return validate_text_column(values)
    elif fieldType == "boolean":
        print("Boolean Validation Triggered")
    elif fieldType == "foreign_key":
        print("FK Validation Triggered")
    elif fieldType == "multi_select":
        print("Multi Validation Triggered")
    elif fieldType == "number":
        print("Number Validation Triggered")
        validate_number_column(values)
        return validate_number_column(values)
    elif fieldType == "select":
        print("Select Validation Triggered")
    elif fieldType == "textarea":
        print("Textarea Validation Triggered")
        validate_textarea_column(values)
        return validate_textarea_column(values)
    else:
        print("no validation for this datatype")


def validate_text_column(values):
    valid = invalid = blank = warning = 0
    for v in values:
        if not v or v.strip() == "":
            blank += 1
            continue
        if len(v) > 1000:
            invalid += 1
        else:
            valid += 1
        # warning check based on common identifiers 
        if any([
            re.search(r"\{.*?\}", v),                 # JSON
            re.search(r"<[a-z][\s\S]*?>", v),         # HTML tags
            re.search(r"#+\s", v)                     # markdown headers
        ]):
            warning += 1
    return {
        "valid": valid,
        "invalid": invalid,
        "blank": blank,
        "warning": warning
    }
def validate_textarea_column(values):
    # Use CSV module's default field size limit
    max_size = csv.field_size_limit()  # default ~131072 bytes

    valid = invalid = blank = warning = 0
    for v in values:
        # Blank or whitespace-only
        if not v or v.strip() == "":
            blank += 1
            continue

        # Invalid if over CSV field limit
        if len(v) > max_size:
            invalid += 1
        else:
            valid += 1

        # Warning: JSON-like content
        if re.search(r"\{.*?\}", v):
            warning += 1

    return {
        "valid": valid,
        "invalid": invalid,
        "blank": blank,
        "warning": warning
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
