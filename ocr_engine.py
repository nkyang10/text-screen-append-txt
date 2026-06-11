"""OCR engine wrapper – delegates to RapidOCR.

RapidOCR_ is an ONNX-based OCR engine that supports Chinese (simplified &
traditional) and English out of the box.  Models are downloaded automatically
on first use.

.. _RapidOCR: https://github.com/RapidAI/RapidOCR
"""

from __future__ import annotations

import logging

import numpy as np
from PIL import Image

from config import AppConfig


class OCREngine:
    """Thin wrapper around ``rapidocr_onnxruntime.RapidOCR``.

    Usage::

        engine = OCREngine(config, logger)
        text = engine.recognize_text_only(pil_image)
    """

    def __init__(self, config: AppConfig, logger: logging.Logger) -> None:
        self.config = config
        self.logger = logger
        self._engine = None

    def warm(self) -> None:
        """Import and instantiate the RapidOCR engine.

        Models are downloaded automatically to ``~/.rapidocr/`` on first use.
        This may take several seconds. Call this after the GUI is visible to
        avoid blocking startup.
        """
        if self._engine is not None:
            return
        try:
            from rapidocr_onnxruntime import RapidOCR

            logger = self.logger
            logger.info("Initialising RapidOCR (models may download on first run)...")
            self._engine = RapidOCR()
            logger.info(
                "RapidOCR ready  |  languages: Chinese (simplified, traditional), English"
            )
        except ImportError:
            self.logger.exception("rapidocr-onnxruntime is not installed")
            raise SystemExit(
                "Missing dependency: rapidocr-onnxruntime\n"
                "  Install with:  pip install rapidocr-onnxruntime"
            ) from None
        except Exception:
            self.logger.exception("RapidOCR initialisation failed")
            raise

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def recognize(self, image: Image.Image):
        """Run OCR on a PIL ``Image``.

        Parameters
        ----------
        image:
            RGB image (will be converted to a numpy array internally).

        Returns
        -------
        list[tuple[str, float]]
            ``(text, confidence)`` pairs, sorted left-to-right top-to-bottom.
            May be empty.
        """
        if self._engine is None:
            self.warm()
        img_array = np.array(image)
        try:
            result, elapse = self._engine(img_array)
            if result is None:
                self.logger.debug("OCR returned None (no text found)")
                return []
            texts = [(text, conf) for (_, text, conf) in result]
            self.logger.debug("OCR: %d blocks in %.2fs", len(texts), elapse)
            return texts
        except Exception:
            self.logger.exception("OCR recognition error")
            return []

    def recognize_text_only(self, image: Image.Image) -> str:
        """Run OCR and return a single concatenated string.

        Only blocks with confidence **>= 0.3** are kept.  Blocks are joined
        with ``\\n``.
        """
        results = self.recognize(image)
        lines = [t for t, c in results if c >= 0.3]
        return "\n".join(lines)
