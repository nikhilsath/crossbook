import os
import sys
import logging
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from logging_setup import configure_logging


class MockApp:
    def __init__(self):
        self.logger = logging.getLogger('mock_app')
        self.logger.handlers.clear()


def test_configure_logging_attaches_handlers_and_sets_level():
    app = MockApp()
    root_logger = logging.getLogger()
    original_handlers = root_logger.handlers[:]
    original_level = root_logger.level

    cfg_rows = [
        {"key": "log_level", "value": "WARNING"},
        {"key": "handler_type", "value": "stream"},
    ]

    try:
        with patch('logging_setup.get_config_rows', return_value=cfg_rows):
            configure_logging(app)

        assert len(app.logger.handlers) >= 2
        assert app.logger.level == logging.WARNING
        assert root_logger.level == logging.WARNING
        assert len(root_logger.handlers) == 1
    finally:
        root_logger.handlers = original_handlers
        root_logger.setLevel(original_level)
        app.logger.handlers.clear()
