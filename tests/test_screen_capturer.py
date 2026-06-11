"""Tests for ScreenCapturer with mocked mss."""

from __future__ import annotations

from unittest.mock import MagicMock, Mock, patch

import pytest
from PIL import Image

from screen_capture import ScreenCapturer
from tests.conftest import app_config, logger


class TestScreenCapturer:
    @patch("screen_capture.mss")
    def test_capture_one_returns_pil_image_of_correct_size(self, mock_mss, app_config, logger):
        mock_sct_img = MagicMock()
        mock_sct_img.width = 100
        mock_sct_img.height = 50
        mock_sct_img.bgra = bytes([0, 0, 0, 255]) * (100 * 50)

        mock_sct = MagicMock()
        mock_sct.grab.return_value = mock_sct_img
        mock_mss.mss.return_value = mock_sct

        capturer = ScreenCapturer((0, 0, 100, 50), app_config, logger)
        result = capturer.capture_one()

        assert result.size == (100, 50)

    @patch("screen_capture.Thread")
    @patch("screen_capture.mss")
    def test_start_creates_daemon_thread(self, mock_mss, mock_thread, app_config, logger):
        mock_mss.mss.return_value = MagicMock()

        capturer = ScreenCapturer((0, 0, 100, 50), app_config, logger)
        capturer.start(callback=Mock())

        assert mock_thread.call_args.kwargs.get("daemon") is True

    @patch("screen_capture.mss")
    def test_stop_sets_stop_event(self, mock_mss, app_config, logger):
        mock_mss.mss.return_value = MagicMock()

        capturer = ScreenCapturer((0, 0, 100, 50), app_config, logger)
        capturer.stop()

        assert capturer._stop.is_set()

    @patch("screen_capture.mss")
    def test_capture_one_calls_grab_with_correct_region(self, mock_mss, app_config, logger):
        mock_sct_img = MagicMock()
        mock_sct_img.width = 100
        mock_sct_img.height = 50
        mock_sct_img.bgra = bytes([0, 0, 0, 255]) * (100 * 50)

        mock_sct = MagicMock()
        mock_sct.grab.return_value = mock_sct_img
        mock_mss.mss.return_value = mock_sct

        capturer = ScreenCapturer((10, 20, 100, 50), app_config, logger)
        capturer.capture_one()

        expected_region = {"left": 10, "top": 20, "width": 100, "height": 50}
        assert mock_sct.grab.call_args[0][0] == expected_region
