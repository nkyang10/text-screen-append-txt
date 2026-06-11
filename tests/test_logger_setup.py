"""Tests for logger_setup.setup_logger."""

import logging
import tempfile
from pathlib import Path

from logger_setup import setup_logger


def test_setup_logger_returns_logger_instance():
    logger = setup_logger(name="test_returns_logger")
    assert isinstance(logger, logging.Logger)


def test_setup_logger_has_correct_name():
    logger = setup_logger(name="my_custom_name")
    assert logger.name == "my_custom_name"


def test_setup_logger_debug_mode_true_sets_level_debug():
    logger = setup_logger(name="test_debug_true", debug_mode=True)
    assert logger.level == logging.DEBUG


def test_setup_logger_debug_mode_false_sets_level_info():
    logger = setup_logger(name="test_debug_false", debug_mode=False)
    assert logger.level == logging.INFO


def test_setup_logger_creates_log_file_when_provided():
    with tempfile.TemporaryDirectory() as td:
        log_path = Path(td) / "test.log"
        logger = setup_logger(name="test_file_create", log_file=log_path)
        file_exists = log_path.exists()
        for handler in logger.handlers:
            handler.close()
        assert file_exists


def test_setup_logger_writes_log_message_to_file():
    with tempfile.TemporaryDirectory() as td:
        log_path = Path(td) / "test.log"
        logger = setup_logger(name="test_file_write", log_file=log_path)
        logger.info("Hello from test")
        for handler in logger.handlers:
            handler.close()
        content = log_path.read_text(encoding="utf-8")
        assert "Hello from test" in content
