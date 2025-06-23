import re

def to_identifier(name: str, prefix: str = "") -> str:
    """Convert arbitrary string to a safe SQL identifier.

    Replaces non-alphanumeric characters with underscores and lowers the
    result. If the identifier starts with a digit, prefix it with the
    provided prefix (defaults to an underscore).
    """
    if not name:
        return ""
    ident = re.sub(r"\W+", "_", name).strip("_").lower()
    if not ident:
        return ""
    if ident[0].isdigit():
        ident = f"{prefix or '_'}{ident}"
    return ident
