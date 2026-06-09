"""Screen capture: area selection overlay and continuous region capture.

Two main classes:

* :class:`AreaSelector` – a fullscreen transparent overlay that lets the
  user drag a rectangle over the subtitle region.
* :class:`ScreenCapturer` – captures that region repeatedly on a background
  thread, skipping frames whose pixel hash has not changed.
"""

from __future__ import annotations

import tkinter as tk
from threading import Event, Thread
from time import sleep

import mss
from PIL import Image

from config import AppConfig


# ===========================================================================
#  Area selection overlay
# ===========================================================================


class AreaSelector:
    """Fullscreen overlay for selecting a screen region.

    Usage::

        selector = AreaSelector(config, logger)
        area = selector.select()          # blocks until user selects / ESC
        if area:                          # (left, top, width, height)
            ...
    """

    def __init__(self, config: AppConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self._result: tuple[int, int, int, int] | None = None

    def select(self) -> tuple[int, int, int, int] | None:
        """Show the overlay and wait for user input.

        Returns
        -------
        ``(left, top, width, height)`` in screen pixels, or ``None`` if the
        user pressed ESC.
        """
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screen_w = monitor["width"]
            screen_h = monitor["height"]

        self.logger.info("Overlay screen size: %dx%d", screen_w, screen_h)

        root = tk.Toplevel()
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        root.configure(bg="black")
        root.attributes("-alpha", 0.15)

        canvas = tk.Canvas(root, bg="black", highlightthickness=0, cursor="cross")
        canvas.pack(fill=tk.BOTH, expand=True)

        canvas.create_text(
            screen_w // 2,
            30,
            text=self.config.OVERLAY_TEXT,
            fill="white",
            font=("Arial", 14, "bold"),
        )

        rect_id: int | None = None
        start_x = start_y = 0

        def _on_press(evt: tk.Event) -> None:
            nonlocal start_x, start_y, rect_id
            start_x, start_y = evt.x_root, evt.y_root
            if rect_id is not None:
                canvas.delete(rect_id)
                rect_id = None

        def _on_drag(evt: tk.Event) -> None:
            nonlocal rect_id
            if rect_id is not None:
                canvas.delete(rect_id)
            rect_id = canvas.create_rectangle(
                start_x,
                start_y,
                evt.x_root,
                evt.y_root,
                outline=self.config.SELECTION_BORDER_COLOR,
                width=self.config.SELECTION_BORDER_WIDTH,
            )

        def _on_release(evt: tk.Event) -> None:
            nonlocal rect_id
            x1, x2 = sorted((start_x, evt.x_root))
            y1, y2 = sorted((start_y, evt.y_root))
            w, h = x2 - x1, y2 - y1
            if w < 10 or h < 10:
                self.logger.debug("Selection too small, ignoring")
                return
            self._result = (x1, y1, w, h)
            self.logger.info("Area selected: (%d, %d) %dx%d", x1, y1, w, h)
            root.destroy()

        def _on_escape(_evt: tk.Event | None = None) -> None:
            self._result = None
            self.logger.info("Area selection cancelled (ESC)")
            root.destroy()

        canvas.bind("<ButtonPress-1>", _on_press)
        canvas.bind("<B1-Motion>", _on_drag)
        canvas.bind("<ButtonRelease-1>", _on_release)
        canvas.bind("<Escape>", _on_escape)
        root.bind("<Escape>", _on_escape)
        canvas.focus_set()

        root.wait_window()
        return self._result


# ===========================================================================
#  Continuous region capturer
# ===========================================================================


class ScreenCapturer:
    """Captures a fixed screen region on a background thread.

    Only invokes the callback when the frame content changes (detected via
    a simple ``hash()`` of the raw pixel data).
    """

    def __init__(
        self,
        area: tuple[int, int, int, int],
        config: AppConfig,
        logger: logging.Logger,
    ) -> None:
        self.area = area
        self.config = config
        self.logger = logger

        self._stop = Event()
        self._sct = mss.mss()
        self._region = {
            "left": area[0],
            "top": area[1],
            "width": area[2],
            "height": area[3],
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def start(self, callback) -> None:
        """Begin capturing in a daemon thread.

        Parameters
        ----------
        callback:
            A callable ``callback(pil_image: PIL.Image.Image)`` invoked
            for every *changed* frame.
        """
        self._stop.clear()
        Thread(target=self._loop, args=(callback,), daemon=True).start()
        self.logger.info(
            "Capturer started: region=(%d,%d) %dx%d  interval=%.1fs",
            *self.area,
            self.config.CAPTURE_INTERVAL_SEC,
        )

    def stop(self) -> None:
        """Signal the capture thread to exit."""
        self._stop.set()
        self.logger.info("Capturer stopped")

    def capture_one(self) -> Image.Image:
        """Grab a single frame synchronously (useful for testing)."""
        sct_img = self._sct.grab(self._region)
        return Image.frombytes(
            "RGB",
            (sct_img.width, sct_img.height),
            sct_img.bgra,
            "raw",
            "BGRX",
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _loop(self, callback) -> None:
        last_hash: int | None = None
        while not self._stop.is_set():
            try:
                sct_img = self._sct.grab(self._region)
                img = Image.frombytes(
                    "RGB",
                    (sct_img.width, sct_img.height),
                    sct_img.bgra,
                    "raw",
                    "BGRX",
                )

                current_hash = hash(img.tobytes())
                if current_hash != last_hash:
                    last_hash = current_hash
                    callback(img)
                else:
                    self.logger.debug("Frame unchanged, skipping callback")
            except Exception:
                self.logger.exception("Capture loop error")

            sleep(self.config.CAPTURE_INTERVAL_SEC)

        self._sct.close()
