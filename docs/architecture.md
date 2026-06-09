# Architecture

## Overview

**Subtitle Screen Capture → Text** is a Windows desktop application that
continuously OCRs a selected screen region and writes newly recognised
subtitle lines to a timestamped text file.

The design follows a simple **pipeline** pattern:

```
[Screen] → [mss capture] → [image] → [RapidOCR] → [text] → [dedup] → [*.txt]
```

Each stage is isolated in its own module, making it straightforward to
swap components (e.g., replace RapidOCR with a different engine).

---

## Pipeline stages

### 1. Area selection (`screen_capture.AreaSelector`)

A fullscreen `tkinter.Toplevel` is created at 15 % opacity.  The user
drags a rectangle while holding the left mouse button; on release the
coordinates are captured.  ESC closes the overlay and returns ``None``.

### 2. Screen capture (`screen_capture.ScreenCapturer`)

Uses the **mss** library (a fast cross-platform framebuffer reader) to
grab the selected region every ``CAPTURE_INTERVAL_SEC`` seconds.

Each frame is hashed (``hash(pixels.tobytes())``) and compared to the
previous frame.  Unchanged frames are skipped to avoid useless OCR work.

### 3. OCR (`ocr_engine.OCREngine`)

Wraps **RapidOCR** (``rapidocr-onnxruntime``), which bundles detection
(DB-Net) and recognition (CRNN + CTC) models exported to ONNX.

The engine accepts a numpy array (RGB) and returns a list of
``(bounding_box, text, confidence)`` tuples.

### 4. Deduplication (`text_dedup.TextDeduplicator`)

A **dual-strategy** deduplicator:

- **Global seen-set**: Every line ever written to the output is stored in
  a Python ``set``.  Lines that already exist are never written again.
- **Rolling window fuzzy comparison**: The last *N* full-text results are
  kept in a ``deque``.  New text is compared against each via
  ``difflib.SequenceMatcher``.  If the similarity ratio exceeds
  ``DEDUP_SIMILARITY_THRESHOLD``, only the lines that are absent from the
  global seen-set are extracted and written.

### 5. Output (`main.py` → direct file I/O)

New lines are appended to ``output/{YYYYMMDD_HHmmss}.txt`` in UTF-8.

---

## Threading model

```
┌────────────────────────────────────────────────────────┐
│                    Main thread                         │
│              (tkinter event loop)                      │
│                                                        │
│  Start btn ──▶ AreaSelector.select() (blocking)       │
│                      │                                 │
│                      ▼                                 │
│            ScreenCapturer.start(callback)              │
│                      │                                 │
│                      ▼                                 │
│         ┌──────────────────────────┐                   │
│         │   Background daemon      │                   │
│         │   thread                 │                   │
│         │                          │                   │
│         │   while not stop:        │                   │
│         │     img = mss.grab()     │                   │
│         │     if img changed:      │                   │
│         │       callback(img)      │                   │
│         │     sleep(interval)      │                   │
│         └──────────────────────────┘                   │
│                      │                                 │
│             callback runs on main                      │
│             thread (via tkinter thread                 │
│             safety: root.after() used)                 │
└────────────────────────────────────────────────────────┘
```

The capture loop runs on a **daemon thread** so it exits automatically when
the main window is closed.  GUI updates from the callback are dispatched
with ``root.after()`` to stay thread-safe.

---

## Data flow (detailed)

```
User clicks "Start Capture"
        │
        ▼
AreaSelector.select()
  ┌──────────────────┐
  │ Fullscreen       │
  │ transparent      │
  │ overlay          │
  │ (tkinter)        │
  └────────┬─────────┘
           │ user drags rectangle
           ▼
(x, y, w, h) ──▶ Confirmation dialog
                       │
                       ▼ Yes
              ScreenCapturer.start()
                       │
                       ▼ (background thread)
              ┌─────────────────────┐
              │ mss.grab(region)    │
              │ PIL.Image.frombytes │
              │ hash(frame)         │
              │ if changed → cb(img)│
              │ sleep(1 s)          │
              └──────────┬──────────┘
                         │
                         ▼ (main thread callback)
              ┌─────────────────────┐
              │ Save debug image    │
              │ (if DEBUG_MODE)     │
              │                     │
              │ ocr.recognize(img)  │
              │  ──▶ numpy array    │
              │  ──▶ RapidOCR       │
              │  ──▶ list[(text,c)] │
              │                     │
              │ dedup.get_new(txt)  │
              │  ──▶ clean text     │
              │  ──▶ fuzzy compare  │
              │  ──▶ extract fresh  │
              │                     │
              │ if new_text:        │
              │   append to *.txt   │
              │   update counter    │
              └─────────────────────┘
```

---

## Module dependency graph

```
main.py
  ├── config.py         (reads AppConfig)
  ├── logger_setup.py   (uses config.LOG_DIR)
  ├── screen_capture    (uses config, mss, PIL)
  │   ├── AreaSelector
  │   └── ScreenCapturer
  ├── ocr_engine        (uses rapidocr-onnxruntime, PIL → numpy)
  └── text_dedup        (no external deps – pure Python)
```

---

## Performance considerations

| Bottleneck | Mitigation |
|------------|-----------|
| **OCR latency** (~200–400 ms for a small region on CPU) | Frame-hash skip avoids calling OCR on identical frames. |
| **Debug image I/O** | Each frame is a small PNG (~50–200 KB for a subtitle bar); saved asynchronously.  Disable with ``--no-debug``. |
| **mss capture** (~5–15 ms) | Fast enough for 1+ FPS. |
| **tkinter overlay** | Only rendered once during area selection. |

---

## Future improvements

- [ ] Configurable OCR languages via the GUI or ``config.py``.
- [ ] Export dedup statistics (total lines seen, unique, etc.).
- [ ] Hotkey to toggle recording without clicking the GUI.
- [ ] Optional timestamp prefix on each output line.
- [ ] Multi-monitor support for area selection.
