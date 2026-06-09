"""Subtitle Screen Capture – OCR-based subtitle logging tool."""

from config import AppConfig
from logger_setup import setup_logger
from screen_capture import AreaSelector, ScreenCapturer
from ocr_engine import OCREngine
from text_dedup import TextDeduplicator

__version__ = "1.0.0"
