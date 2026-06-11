"""Integration tests for the full capture -> OCR -> dedup -> write pipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from ocr_engine import OCREngine
from text_dedup import TextDeduplicator
from tests.conftest import app_config, blank_image, logger, temp_output_file


class TestPipeline:
    @patch("rapidocr_onnxruntime.RapidOCR")
    def test_pipeline_flow_writes_new_text_to_output_file(
        self, mock_ocr, app_config, logger, blank_image, temp_output_file
    ):
        mock_ocr.return_value.return_value = (
            [([[0, 0, 10, 10]], "Hello world", 0.95)],
            0.1,
        )
        ocr = OCREngine(app_config, logger)
        dedup = TextDeduplicator()
        text = ocr.recognize_text_only(blank_image)
        new_text = dedup.get_new_text(text)
        with open(temp_output_file, "a", encoding="utf-8") as fh:
            fh.write(new_text + "\n")
        assert temp_output_file.read_text(encoding="utf-8") == "Hello world\n"

    @patch("rapidocr_onnxruntime.RapidOCR")
    def test_pipeline_dedup_prevents_duplicate_write(
        self, mock_ocr, app_config, logger, blank_image, temp_output_file
    ):
        mock_ocr.return_value.return_value = (
            [([[0, 0, 10, 10]], "Same text", 0.95)],
            0.1,
        )
        ocr = OCREngine(app_config, logger)
        dedup = TextDeduplicator()
        for _ in range(2):
            text = ocr.recognize_text_only(blank_image)
            new_text = dedup.get_new_text(text)
            if new_text:
                with open(temp_output_file, "a", encoding="utf-8") as fh:
                    fh.write(new_text + "\n")
        assert temp_output_file.read_text(encoding="utf-8") == "Same text\n"

    @patch("rapidocr_onnxruntime.RapidOCR")
    def test_pipeline_empty_ocr_result_skips_file_write(
        self, mock_ocr, app_config, logger, blank_image, temp_output_file
    ):
        temp_output_file.write_text("", encoding="utf-8")
        mock_ocr.return_value.return_value = (None, 0.0)
        ocr = OCREngine(app_config, logger)
        dedup = TextDeduplicator()
        text = ocr.recognize_text_only(blank_image)
        new_text = dedup.get_new_text(text)
        if new_text:
            with open(temp_output_file, "a", encoding="utf-8") as fh:
                fh.write(new_text + "\n")
        assert temp_output_file.read_text(encoding="utf-8") == ""
