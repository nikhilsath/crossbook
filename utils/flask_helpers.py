import time
from flask import g, request, current_app


def start_timer():
    """Record the start time of the request and log the request start."""
    g.start_time = time.time()
    current_app.logger.debug(f"[REQ] {request.method} {request.path} started")


def log_request(response):
    """Log the duration and status code of the completed request."""
    duration = time.time() - g.get("start_time", time.time())
    current_app.logger.debug(
        f"[REQ] {request.method} {request.path} completed in {duration:.3f}s with {response.status_code}"
    )
    return response


def log_exception(exc):
    """Log any exception raised during the request lifecycle."""
    if exc:
        current_app.logger.exception(
            f"[ERROR] Unhandled exception during {request.method} {request.path}: {exc}"
        )
