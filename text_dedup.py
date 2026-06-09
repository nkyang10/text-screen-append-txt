"""Text deduplication – minimise repeated subtitle lines in the output.

The :class:`TextDeduplicator` keeps:

#. A **rolling window** of the last *N* full OCR results for fuzzy
   similarity comparison.
#. A **global set** of every unique line that has already been written
   to the output file.

When new text arrives, any line already present in the global set is
silently dropped.  If the text resembles a recent entry above the similarity
threshold, only the truly new lines are extracted.
"""

from __future__ import annotations

import difflib
from collections import deque


class TextDeduplicator:
    """Filters subtitle text so that duplicate lines are not appended twice.

    Parameters
    ----------
    window_size:
        Number of recent full-text results retained for fuzzy comparison.
    threshold:
        ``SequenceMatcher`` ratio threshold (0–1).  When a new text scores
        above this against any recent entry, only the *new* lines are kept.
    """

    def __init__(self, window_size: int = 10, threshold: float = 0.85) -> None:
        self.window_size = window_size
        self.threshold = threshold
        self._history: deque[str] = deque(maxlen=window_size)
        self._seen_lines: set[str] = set()
        self._last_appended: str = ""

    # ------------------------------------------------------------------
    #  Public API
    # ------------------------------------------------------------------

    def get_new_text(self, raw_text: str) -> str | None:
        """Return the portion of ``raw_text`` that should be written.

        * ``None`` means nothing new to write (fully duplicate).
        * A non-empty string contains only lines that have not been seen
          before.
        """
        if not raw_text or not raw_text.strip():
            return None

        cleaned = self._clean(raw_text)
        if not cleaned:
            return None

        # Exact-match shortcut
        if cleaned == self._last_appended:
            return None

        # Fuzzy check against recent history
        for prev in self._history:
            ratio = difflib.SequenceMatcher(None, cleaned, prev).ratio()
            if ratio > self.threshold:
                new_lines = self._fresh_lines(cleaned)
                if new_lines:
                    result = "\n".join(new_lines)
                    self._update(cleaned, result)
                    return result
                return None

        # Fully new text
        new_lines = self._fresh_lines(cleaned)
        if not new_lines:
            return None
        result = "\n".join(new_lines)
        self._update(cleaned, result)
        return result

    def reset(self) -> None:
        """Clear all internal state (call before starting a new session)."""
        self._history.clear()
        self._seen_lines.clear()
        self._last_appended = ""

    # ------------------------------------------------------------------
    #  Internal helpers
    # ------------------------------------------------------------------

    def _clean(self, text: str) -> str:
        """Strip whitespace and remove duplicate lines within *text*."""
        lines = []
        seen = set()
        for line in text.strip().split("\n"):
            s = line.strip()
            if s and s not in seen:
                seen.add(s)
                lines.append(s)
        return "\n".join(lines)

    def _fresh_lines(self, cleaned: str) -> list[str]:
        """Return lines from *cleaned* that have never been seen."""
        return [l for l in cleaned.split("\n") if l not in self._seen_lines]

    def _update(self, cleaned: str, appended: str) -> None:
        self._history.append(cleaned)
        self._last_appended = cleaned
        self._seen_lines.update(appended.split("\n"))
