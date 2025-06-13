import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from db.config import get_logging_config


def configure_logging(app):
    """Configure application logging based on DB settings."""
    cfg = get_logging_config()

    # Clear existing handlers that Flask may have added
    app.logger.handlers.clear()

    level_name = cfg.get("log_level")
    level = getattr(logging, level_name.upper(), logging.INFO) if level_name else logging.INFO

    handler_type = cfg.get("handler_type", "stream")
    filename = cfg.get("filename", "crossbook.log")
    max_bytes = int(cfg.get("max_file_size") or 0)
    backup = int(cfg.get("backup_count") or 0)
    when_interval = cfg.get("when_interval")
    interval = int(cfg.get("interval_count") or 0)
    log_fmt = cfg.get(
        "log_format",
        "[%(asctime)s] %(levelname)s in %(module)s:%(funcName)s: %(message)s",
    )

    if handler_type == "rotating":
        import os

        log_dir = os.path.dirname(filename)
        if log_dir and not os.path.isdir(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            filename,
            maxBytes=max_bytes,
            backupCount=backup
        )
    elif handler_type == "timed":
        file_handler = TimedRotatingFileHandler(
            filename,
            when=when_interval,
            interval=interval,
            backupCount=backup
        )
    else:  # default to 'stream'
        file_handler = logging.StreamHandler()

    formatter = logging.Formatter(log_fmt)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    # Only show errors in the console but keep all logs in the file
    console_handler.setLevel(logging.ERROR)

    app.logger.setLevel(level)
    app.logger.addHandler(file_handler)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(level)
    root_logger.addHandler(file_handler)
    root_logger.propagate = False

    app.logger.addHandler(console_handler)
    app.logger.propagate = False

