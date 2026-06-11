from pathlib import Path

from config import AppConfig


def test_app_name_is_subtitle_screen_capture():
    assert AppConfig.APP_NAME == "Subtitle Screen Capture"


def test_app_version_is_1_0_0():
    assert AppConfig.APP_VERSION == "1.0.0"


def test_base_dir_exists():
    assert AppConfig.BASE_DIR.exists()


def test_output_dir_parent_exists():
    assert AppConfig.OUTPUT_DIR.parent.exists()


def test_debug_dir_parent_exists():
    assert AppConfig.DEBUG_DIR.parent.exists()


def test_log_dir_parent_exists():
    assert AppConfig.LOG_DIR.parent.exists()


def test_capture_interval_is_positive():
    assert AppConfig.CAPTURE_INTERVAL_SEC > 0


def test_capture_interval_is_float():
    assert isinstance(AppConfig.CAPTURE_INTERVAL_SEC, float)


def test_dedup_similarity_threshold_is_between_zero_and_one():
    assert 0 <= AppConfig.DEDUP_SIMILARITY_THRESHOLD <= 1


def test_output_dir_is_path_object():
    assert isinstance(AppConfig.OUTPUT_DIR, Path)


def test_debug_dir_is_path_object():
    assert isinstance(AppConfig.DEBUG_DIR, Path)


def test_log_dir_is_path_object():
    assert isinstance(AppConfig.LOG_DIR, Path)
