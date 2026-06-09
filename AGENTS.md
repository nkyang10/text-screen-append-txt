# AGENTS.md — AI-Agent-Friendly Reference

This file helps LLM-powered coding assistants (Copilot, Codeium, etc.)
understand the project structure, conventions, and common tasks.

---

## Project overview

A Windows desktop app that captures a user-selected screen region, runs
OCR every second, deduplicates the text, and appends it to a ``.txt`` file.

- **Language:** Python 3.10+
- **GUI framework:** tkinter (built-in)
- **OCR engine:** RapidOCR (``rapidocr-onnxruntime``)
- **Screen capture:** mss

---

## File structure

```
text-screen-append-txt/
├── main.py              # Entry point, GUI, pipeline orchestration
├── config.py            # AppConfig dataclass – all tunable parameters
├── logger_setup.py      # setup_logger() – returns configured logger
├── screen_capture.py    # AreaSelector + ScreenCapturer classes
├── ocr_engine.py        # OCREngine wrapping RapidOCR
├── text_dedup.py        # TextDeduplicator – rolling window + seen-set
└── __init__.py          # Package init, version
```

---

## Key classes & functions

### `main.py`
| Symbol | Role |
|--------|------|
| `SubtitleCaptureApp` | Owns the tkinter root window, handles button callbacks, creates capturer / OCR / dedup instances. |
| `SubtitleCaptureApp._on_capture(image)` | The hot path: save debug frame → OCR → dedup → write. |

### `screen_capture.py`
| Symbol | Role |
|--------|------|
| `AreaSelector` | Fullscreen transparent overlay, blocks until user selects or ESC. |
| `AreaSelector.select()` | Returns `(left, top, width, height)` or `None`. |
| `ScreenCapturer` | Daemon-threaded region capturer. |
| `ScreenCapturer.start(callback)` | Launches capture thread. |
| `ScreenCapturer.capture_one()` | Synchronous frame grab (for testing). |

### `ocr_engine.py`
| Symbol | Role |
|--------|------|
| `OCREngine` | Wraps `RapidOCR`; downloads models on first use. |
| `OCREngine.recognize(image)` | Returns `list[(text, confidence)]`. |
| `OCREngine.recognize_text_only(image)` | Returns concatenated string (confidence ≥ 0.3). |

### `text_dedup.py`
| Symbol | Role |
|--------|------|
| `TextDeduplicator` | Tracks all seen lines and a rolling window of recent full texts. |
| `get_new_text(raw_text)` | Returns only the portion of text that hasn't been seen before, or `None`. |
| `reset()` | Clears all state. |

---

## Configuration

Edit `config.py` → `AppConfig`. Key knobs:

```
CAPTURE_INTERVAL_SEC = 1.0       # Seconds between captures
DEDUP_SIMILARITY_THRESHOLD = 0.85  # Fuzzy match cutoff (0–1)
DEBUG_MODE = True                 # Save frames to debug/
```

---

## Common development tasks

### Adding a new OCR engine

1. Create a new class following the `OCREngine` interface:
   ```python
   class MyEngine:
       def recognize_text_only(self, image: PIL.Image) -> str: ...
   ```
2. Swap the instantiation in `SubtitleCaptureApp.__init__()`.

### Changing the dedup algorithm

Edit `TextDeduplicator` in `text_dedup.py`. The contract is:
```python
def get_new_text(self, raw_text: str) -> str | None
```

### Adding a configurable option

1. Add an attribute to `AppConfig` in `config.py`.
2. Read it wherever needed (all modules receive `config` in their constructor).

---

## Conventions

- **Type hints** everywhere (PEP 484).
- **`logging` over `print`** – every module receives a ``logger``.
- **Snake_case** for methods/variables, **PascalCase** for classes.
- **Private** members prefixed with underscore (`_`).
- **No comments inside function bodies** – use descriptive names instead.
- **Thread safety**: GUI updates via ``root.after()``, not direct calls.

---

## Testing

No test framework is configured yet.  To run a quick smoke test:

```bash
python -c "
from screen_capture import ScreenCapturer
from config import AppConfig
from logger_setup import setup_logger
logger = setup_logger(debug_mode=False)
# Test capture on a 100x100 region at (0,0)
c = ScreenCapturer((0, 0, 100, 100), AppConfig(), logger)
img = c.capture_one()
print(f'Captured {img.size}')
"
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `ModuleNotFoundError: No module named 'rapidocr_onnxruntime'` | Missing dependency | `pip install rapidocr-onnxruntime` |
| OCR returns empty text | Region too small / no text visible | Check `debug/frame_*.png` to verify the captured region. |
| FPS is too low | OCR is CPU-bound | Increase `CAPTURE_INTERVAL_SEC` in config. |
| GUI freezes during area selection | `AreaSelector.select()` is blocking | By design – selection is modal. |
| Overlay not showing | DPI / multi-monitor | Ensure ``SetProcessDpiAwareness(1)`` is called (done in ``main()``). |
