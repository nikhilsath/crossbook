"""Value normalizers that convert raw input into a canonical stored form.

Each normalizer accepts a single raw value and returns a string suitable for
database storage.
"""

import logging

logger = logging.getLogger(__name__)


def normalize_boolean(value) -> str:
    """Return '1' for truthy boolean strings, '0' otherwise."""
    return "1" if str(value).lower() in {"1", "true", "on", "yes"} else "0"


def normalize_number(value) -> str:
    """Return a float string for numeric values, '0' on failure."""
    try:
        return str(float(value))
    except (TypeError, ValueError):
        logger.warning("Failed to normalize number", exc_info=True)
        return "0"


def normalize_multi(value) -> str:
    """Return a comma-separated string for multi-value fields."""
    if isinstance(value, (list, tuple, set)):
        return ", ".join(str(v) for v in value)
    return "" if value is None else str(value)
