"""Logging configuration for the application.

Provides a single ``setup_logger`` function that returns a configured
:class:`logging.Logger` instance with console + rotating file handlers.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(
    name: str = "capture_app",
    debug_mode: bool = True,
    log_dir: Path | None = None,
    log_file: Path | None = None,
) -> logging.Logger:
    """Configure and return a logger instance.

    Parameters
    ----------
    name:
        Logger name (used to retrieve the same logger elsewhere).
    debug_mode:
        If ``True`` the logger level is ``DEBUG``, otherwise ``INFO``.
    log_dir:
        Directory for the rotating log file.  Ignored if ``log_file`` is set.
    log_file:
        Full path to the log file.  If omitted a default is created in
        ``log_dir``.

    Returns
    -------
    logging.Logger
        Ready-to-use logger.
    """
    level = logging.DEBUG if debug_mode else logging.INFO
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove any pre-existing handlers so we don't duplicate on re-init.
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s  [%(levelname)-8s]  %(name)s:%(lineno)d  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # --- Console handler ---------------------------------------------------
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(level)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # --- Rotating file handler ---------------------------------------------
    if log_dir and log_file is None:
        log_dir = Path(log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "app.log"

    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            str(log_file),
            maxBytes=10_485_760,  # 10 MiB
            backupCount=5,
            encoding="utf-8",
        )
        fh.setLevel(logging.DEBUG)  # Always DEBUG to file
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger
