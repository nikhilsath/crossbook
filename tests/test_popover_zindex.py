import os
import sys
import re
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_popover_dark_has_no_z_index():
    templates_dir = Path(__file__).resolve().parent.parent / "templates"
    pattern = re.compile(r"class=[\'\"]([^\'\"]*popover-dark[^\'\"]*)[\'\"]")
    offending = []

    for file_path in templates_dir.rglob("*.html"):
        text = file_path.read_text()
        for match in pattern.findall(text):
            if re.search(r"\bz-(10|20)\b", match):
                offending.append(f"{file_path}:{match}")

    assert not offending, "z-index class found: \n" + "\n".join(offending)
