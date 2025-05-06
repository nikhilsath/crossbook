import json
import re

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
    elif fieldType == "select":
        print("Select Validation Triggered")
    elif fieldType == "textarea":
        print("Textarea Validation Triggered")
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
