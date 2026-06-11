"""Tests for OCREngine with mocked RapidOCR."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from ocr_engine import OCREngine
from tests.conftest import app_config, blank_image, logger


class TestOCREngine:
    @patch("rapidocr_onnxruntime.RapidOCR")
    def test_recognize_text_only_returns_empty_string_when_ocr_returns_none(
        self, mock_ocr, app_config, logger, blank_image
    ):
        mock_ocr.return_value.return_value = (None, 0.0)
        engine = OCREngine(app_config, logger)
        result = engine.recognize_text_only(blank_image)
        assert result == ""

    @patch("rapidocr_onnxruntime.RapidOCR")
    def test_recognize_returns_empty_list_when_ocr_returns_none(
        self, mock_ocr, app_config, logger, blank_image
    ):
        mock_ocr.return_value.return_value = (None, 0.0)
        engine = OCREngine(app_config, logger)
        result = engine.recognize(blank_image)
        assert result == []

    @patch("rapidocr_onnxruntime.RapidOCR")
    def test_recognize_text_only_filters_low_confidence_results(
        self, mock_ocr, app_config, logger, blank_image
    ):
        mock_ocr.return_value.return_value = (
            [([[0, 0, 10, 10]], "hello", 0.95), ([[0, 0, 10, 10]], "world", 0.2)],
            0.1,
        )
        engine = OCREngine(app_config, logger)
        result = engine.recognize_text_only(blank_image)
        assert result == "hello"

    @patch("rapidocr_onnxruntime.RapidOCR")
    def test_warm_creates_engine_via_recognize_call(
        self, mock_ocr, app_config, logger, blank_image
    ):
        mock_ocr.return_value.return_value = (
            [([[0, 0, 10, 10]], "test", 0.95)],
            0.1,
        )
        engine = OCREngine(app_config, logger)
        engine.recognize(blank_image)
        assert engine._engine is not None

    @patch("rapidocr_onnxruntime.RapidOCR")
    def test_recognize_text_only_concatenates_high_confidence_results_with_newlines(
        self, mock_ocr, app_config, logger, blank_image
    ):
        mock_ocr.return_value.return_value = (
            [([[0, 0, 10, 10]], "line1", 0.95), ([[0, 0, 10, 10]], "line2", 0.85)],
            0.1,
        )
        engine = OCREngine(app_config, logger)
        result = engine.recognize_text_only(blank_image)
        assert result == "line1\nline2"
