import ast
from pathlib import Path

LOG_FUNCS = {"debug", "info", "warning", "error", "critical", "exception"}


def _python_files():
    for path in Path('.').rglob('*.py'):
        if any(part.startswith('.') for part in path.parts):
            # skip hidden directories
            continue
        yield path


def test_no_bare_except_blocks():
    errors = []
    for path in _python_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                errors.append(f"{path}:{node.lineno}")
    assert not errors, "Bare except found:\n" + "\n".join(errors)


def test_logging_calls_in_except_have_context():
    errors = []
    for path in _python_files():
        tree = ast.parse(path.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                for child in ast.walk(node):
                    if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                        attr = child.func.attr
                        if attr in LOG_FUNCS:
                            value = child.func.value
                            is_logger = False
                            if isinstance(value, ast.Name) and value.id == "logger":
                                is_logger = True
                            elif (
                                isinstance(value, ast.Attribute)
                                and value.attr == "logger"
                                and isinstance(value.value, ast.Name)
                            ):
                                is_logger = True
                            if is_logger and attr != "exception":
                                has_kw = any(
                                    k.arg in {"exc_info", "stack_info", "extra"}
                                    for k in child.keywords
                                )
                                if not has_kw:
                                    errors.append(f"{path}:{child.lineno}")
    assert not errors, (
        "Logging calls missing context or traceback in except blocks:\n" + "\n".join(errors)
    )
