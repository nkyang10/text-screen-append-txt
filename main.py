#!/usr/bin/env python3
"""Subtitle Screen Capture – Main Entry Point.

Captures a user-selected screen region in a loop, runs OCR on each frame,
deduplicates the recognised text, and appends new lines to a timestamped
``.txt`` file.

Usage
-----

    # Run with debug mode (default – saves every frame to debug/):
    python main.py

    # Run without debug image saving:
    python main.py --no-debug
"""

from __future__ import annotations

import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from datetime import datetime

from config import AppConfig
from logger_setup import setup_logger
from screen_capture import AreaSelector, ScreenCapturer
from ocr_engine import OCREngine
from text_dedup import TextDeduplicator


class SubtitleCaptureApp:
    """Main application – owns the GUI and orchestrates capture / OCR / dedup.

    Usage::

        app = SubtitleCaptureApp()
        app.run()
    """

    def __init__(self, config: AppConfig | None = None) -> None:
        self.config = config or AppConfig()

        # Ensure runtime directories exist ----------------------------------
        for d in (self.config.OUTPUT_DIR, self.config.DEBUG_DIR, self.config.LOG_DIR):
            d.mkdir(parents=True, exist_ok=True)

        # Logger ------------------------------------------------------------
        self.logger = setup_logger(
            debug_mode=self.config.DEBUG_MODE,
            log_dir=self.config.LOG_DIR,
        )
        self.logger.info(
            "%s v%s starting  |  debug=%s",
            self.config.APP_NAME,
            self.config.APP_VERSION,
            self.config.DEBUG_MODE,
        )

        # OCR engine --------------------------------------------------------
        self.ocr = OCREngine(self.config, self.logger)
        self._ocr_ready = False

        # Deduplicator ------------------------------------------------------
        self.dedup = TextDeduplicator(
            window_size=self.config.DEDUP_WINDOW_SIZE,
            threshold=self.config.DEDUP_SIMILARITY_THRESHOLD,
        )

        # Runtime state -----------------------------------------------------
        self._running: bool = False
        self._capturer: ScreenCapturer | None = None
        self._output_file: Path | None = None
        self._area: tuple[int, int, int, int] | None = None
        self._capture_count = 0
        self._new_count = 0
        self._skip_count = 0
        self._write_error_count = 0

        self._build_gui()

        # Defer OCR engine warm-up so the window appears immediately.
        self.root.after(100, self._defer_ocr_init)

    # ======================================================================
    #  GUI
    # ======================================================================

    def _build_gui(self) -> None:
        self.root = tk.Tk()
        self.root.title(self.config.APP_NAME)
        self.root.geometry(f"{self.config.WINDOW_WIDTH}x{self.config.WINDOW_HEIGHT}")
        self.root.resizable(False, False)

        # Title
        tk.Label(
            self.root, text=self.config.APP_NAME, font=("Arial", 12, "bold")
        ).pack(pady=(10, 0))

        # Status
        self._status_var = tk.StringVar(value="Ready.  Click Start Capture.")
        tk.Label(self.root, textvariable=self._status_var, wraplength=280).pack(pady=5)

        # Selected area info
        self._area_var = tk.StringVar(value="Area: not selected")
        tk.Label(self.root, textvariable=self._area_var, fg="gray").pack()

        # Counter
        self._count_var = tk.StringVar(value="0 captures  |  0 new  |  0 skipped")
        tk.Label(self.root, textvariable=self._count_var, fg="gray").pack()

        # Output path
        self._output_var = tk.StringVar(value="")
        tk.Label(self.root, textvariable=self._output_var, fg="gray", wraplength=300).pack()

        # Start button
        self._start_btn = tk.Button(
            self.root,
            text="Start Capture",
            command=self._on_start,
            width=18,
            height=2,
        )
        self._start_btn.pack(pady=(10, 2))

        # Stop button
        self._stop_btn = tk.Button(
            self.root,
            text="Stop Capture",
            command=self._on_stop,
            width=18,
            height=2,
            state=tk.DISABLED,
        )
        self._stop_btn.pack(pady=2)

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.root.bind("<Control-Return>", lambda _: self._on_start())
        self.root.bind("<Control-period>", lambda _: self._on_stop())

    # ======================================================================
    #  Actions
    # ======================================================================

    def _defer_ocr_init(self) -> None:
        """Warm the OCR engine in background so first capture is fast."""
        self._status_var.set("Initialising OCR engine...")
        self.root.update()
        try:
            self.ocr.warm()
            self._ocr_ready = True
            self._status_var.set("Ready.  Click Start Capture.")
        except Exception:
            self.logger.exception("OCR initialisation failed")
            self._status_var.set("OCR init failed - see logs")
            self._ocr_ready = False

    def _on_start(self) -> None:
        """Initiate area selection, confirm, then begin capture loop."""
        self._status_var.set("Selecting area...")
        self._start_btn.config(state=tk.DISABLED)
        self.root.update()

        # 1. Area selection overlay -----------------------------------------
        selector = AreaSelector(self.config, self.logger)
        area = selector.select()

        if area is None:
            self._status_var.set("Selection cancelled")
            self._start_btn.config(state=tk.NORMAL)
            return

        self._area = area
        self._area_var.set(f"Area: ({area[0]}, {area[1]})  {area[2]}×{area[3]}")

        # 2. Confirmation dialog --------------------------------------------
        if not messagebox.askyesno(
            "Confirm Area",
            f"Use this region for capture?\n\n"
            f"  Left:   {area[0]}\n"
            f"  Top:    {area[1]}\n"
            f"  Width:  {area[2]}\n"
            f"  Height: {area[3]}",
        ):
            self._status_var.set("Selection cancelled")
            self._start_btn.config(state=tk.NORMAL)
            return

        # 3. Prepare output file --------------------------------------------
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._output_file = self.config.OUTPUT_DIR / f"{timestamp}.txt"
        self._output_file.write_text("", encoding="utf-8")
        self.logger.info("Output file: %s", self._output_file)
        self._after_set_output(f"Output: {self._output_file.name}")

        # 4. Reset dedup state ----------------------------------------------
        self.dedup.reset()
        self._capture_count = 0
        self._new_count = 0
        self._skip_count = 0
        self._update_counts()

        # 5. Start capturer -------------------------------------------------
        self._running = True
        self._capturer = ScreenCapturer(area, self.config, self.logger)
        self._capturer.start(self._on_capture)

        self._stop_btn.config(state=tk.NORMAL)
        self._status_var.set("Recording…")
        self.logger.info("Capture session started")

    def _on_stop(self) -> None:
        """Stop the capture loop and reset UI."""
        self._running = False
        if self._capturer:
            self._capturer.stop()

        self._start_btn.config(state=tk.NORMAL)
        self._stop_btn.config(state=tk.DISABLED)
        self._status_var.set("Stopped")
        self.logger.info(
            "Session ended  |  captures=%d  new=%d  skipped=%d",
            self._capture_count,
            self._new_count,
            self._skip_count,
        )

    def _on_capture(self, image) -> None:
        """Process one captured frame: save debug image -> OCR -> dedup -> write."""
        self._capture_count += 1

        if self.config.DEBUG_MODE:
            debug_path = self.config.DEBUG_DIR / f"frame_{self._capture_count:04d}.png"
            try:
                image.save(debug_path)
                self.logger.debug("Saved debug frame %d", self._capture_count)
            except OSError:
                self.logger.exception("Failed to save debug frame #%d", self._capture_count)

        try:
            text = self.ocr.recognize_text_only(image)
        except Exception:
            self.logger.exception("OCR failed on frame #%d", self._capture_count)
            self._after_set_status("OCR error - check logs")
            self._after_update_counts()
            return

        if not text:
            self._skip_count += 1
            self.logger.debug("No text in frame #%d", self._capture_count)
            self._after_update_counts()
            return

        new_text = self.dedup.get_new_text(text)
        if new_text:
            self._new_count += 1
            try:
                with open(self._output_file, "a", encoding="utf-8") as fh:
                    fh.write(new_text + "\n")
                self.logger.info("NEW  [%d] %s", self._new_count, new_text[:120])
                self._after_set_status(f"Captured: {new_text[:60]}...")
            except OSError:
                self._write_error_count += 1
                self.logger.exception("Failed to write output file: %s", self._output_file)
                self._after_set_status("Write error - check disk space")
        else:
            self._skip_count += 1
            self.logger.debug("Duplicate text, skipped")

        self._after_update_counts()

    # ======================================================================
    #  tkinter thread-safe helpers
    # ======================================================================

    def _after_update_counts(self) -> None:
        txt = (
            f"{self._capture_count} captures  |  "
            f"{self._new_count} new  |  "
            f"{self._skip_count} skipped"
        )
        self.root.after(0, lambda: self._count_var.set(txt))

    def _after_set_status(self, msg: str) -> None:
        self.root.after(0, lambda: self._status_var.set(msg))

    def _after_set_output(self, msg: str) -> None:
        self.root.after(0, lambda: self._output_var.set(msg))

    # ======================================================================
    #  Lifecycle
    # ======================================================================

    def _on_close(self) -> None:
        self.logger.info("Application shutting down")
        self._on_stop()
        self.root.destroy()

    def run(self) -> None:
        """Start the tkinter event loop."""
        self.root.mainloop()


# ===========================================================================
#  Entry point
# ===========================================================================


def main() -> None:
    """Parse CLI flags and launch the application."""

    # Enable per-monitor DPI awareness on Windows so tkinter / mss
    # coordinates are consistent.
    if sys.platform == "win32":
        try:
            import ctypes  # noqa: PLC0415

            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:  # noqa: BLE001
            pass  # Best effort – fall back to system default.

    config = AppConfig()
    if "--no-debug" in sys.argv:
        config.DEBUG_MODE = False

    app = SubtitleCaptureApp(config)
    app.run()


if __name__ == "__main__":
    main()
