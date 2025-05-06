import json
import re

def validation_sorter():
    print("✅ Validation function was triggered.")

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
