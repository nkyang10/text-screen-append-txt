"""pytest configuration and shared fixtures."""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

import pytest
from PIL import Image

from config import AppConfig


@pytest.fixture
def app_config() -> AppConfig:
    """Return an AppConfig with temp directories for testing."""
    cfg = AppConfig()
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cfg.OUTPUT_DIR = tmp / "output"
        cfg.DEBUG_DIR = tmp / "debug"
        cfg.LOG_DIR = tmp / "logs"
        cfg.DEBUG_MODE = False
        yield cfg


@pytest.fixture
def logger() -> logging.Logger:
    """Return a logger that writes to a buffer (no console noise)."""
    log = logging.getLogger("test")
    log.setLevel(logging.DEBUG)
    log.handlers.clear()
    handler = logging.NullHandler()
    log.addHandler(handler)
    return log


@pytest.fixture
def blank_image() -> Image.Image:
    """Return a small blank RGB image (simulating a screen capture)."""
    return Image.new("RGB", (100, 30), color=(0, 0, 0))


@pytest.fixture
def text_image() -> Image.Image:
    """Return a small image with white pixels (simulating text presence)."""
    img = Image.new("RGB", (100, 30), color=(0, 0, 0))
    for x in range(10, 90):
        for y in range(5, 25):
            img.putpixel((x, y), (255, 255, 255))
    return img


@pytest.fixture
def temp_output_file() -> Path:
    """Return a path to a temporary output .txt file."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td) / "output.txt"
