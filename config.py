"""Application configuration settings.

All tunable parameters are defined here in one place for easy customization.
"""

from pathlib import Path


class AppConfig:
    """Central configuration for the Subtitle Screen Capture application.

    Attributes:
        APP_NAME: Display name shown in window title.
        APP_VERSION: Semantic version string.
        WINDOW_WIDTH / WINDOW_HEIGHT: Main GUI window dimensions in pixels.
        CAPTURE_INTERVAL_SEC: Seconds between screen captures.
        DEDUP_WINDOW_SIZE: Number of recent OCR results kept for comparison.
        DEDUP_SIMILARITY_THRESHOLD: Ratio (0-1) above which text is considered a
            near-duplicate. Lower = stricter dedup.
        BASE_DIR: Project root directory.
        OUTPUT_DIR: Where captured .txt files are saved.
        DEBUG_DIR: Where debug screenshot images are saved (debug mode only).
        LOG_DIR: Where log files are written.
        DEBUG_MODE: When True, saves every captured frame and logs verbosely.
        LOG_MAX_BYTES: Max size of a single log file before rotation.
        LOG_BACKUP_COUNT: Number of rotated log files to retain.
        OVERLAY_TEXT: Instruction shown on the area-selection overlay.
        SELECTION_BORDER_COLOR: Color of the selection rectangle border.
        SELECTION_BORDER_WIDTH: Thickness of the selection rectangle border.
    """

    APP_NAME = "Subtitle Screen Capture"
    APP_VERSION = "1.0.0"

    # ------------------------------------------------------------------ GUI
    WINDOW_WIDTH = 320
    WINDOW_HEIGHT = 220

    # ------------------------------------------------------------- Capture
    CAPTURE_INTERVAL_SEC = 1.0

    # -------------------------------------------------------------- Dedup
    DEDUP_WINDOW_SIZE = 10
    DEDUP_SIMILARITY_THRESHOLD = 0.85

    # --------------------------------------------------------------- Paths
    BASE_DIR = Path(__file__).parent
    OUTPUT_DIR = BASE_DIR / "output"
    DEBUG_DIR = BASE_DIR / "debug"
    LOG_DIR = BASE_DIR / "logs"

    # --------------------------------------------------------------- Debug
    DEBUG_MODE = True

    # ------------------------------------------------------------- Logging
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
    LOG_BACKUP_COUNT = 5

    # ------------------------------------------------------------- Overlay
    OVERLAY_TEXT = "Drag to select area  |  ESC to cancel"
    SELECTION_BORDER_COLOR = "red"
    SELECTION_BORDER_WIDTH = 2
