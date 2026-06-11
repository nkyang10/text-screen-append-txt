<p align="center">
  <img src="docs/assets/icon.png" alt="Subtitle Screen Capture" width="120"/>
</p>

<h1 align="center">Subtitle Screen Capture → Text</h1>

<p align="center">
  <em>Select a screen region → OCR every second → dedup → append to a <code>.txt</code> file.</em>
  <br>
  Supports Simplified Chinese, Traditional Chinese, and English.
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#usage">Usage</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#faq">FAQ</a>
</p>

---

## Features

- **Region selection** – Fullscreen transparent overlay; drag to select exactly where subtitles appear.
- **Continuous OCR** – Captures the selected region every second and runs RapidOCR (Chinese + English) on it.
- **Smart deduplication** – Avoids writing the same subtitle line twice, even when text scrolls or partially overlaps.
- **Debug mode** – Saves every captured frame as a timestamped PNG in `debug/` for troubleshooting. Enabled by default.
- **Rotating logs** – Verbose logs written to `logs/app.log` with automatic rotation.
- **Minimal GUI** – Start / Stop buttons, live counter, and status display.

---

## Quick Start

### 1. Requirements

- Python 3.10 or later
- Windows 10 / 11 (other OS untested)

### 2. Install

```bash
# Clone
git clone https://github.com/nkyang10/text-screen-append-txt.git
cd text-screen-append-txt

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

> **Note on first run:** RapidOCR will download model files automatically to
> `~\.rapidocr\` on first import. This is a one-time ~50 MB download and may
> take 10–30 seconds.

### 3. Run

```bash
python main.py
```

Or double-click `run.bat` (uses the virtual environment automatically).

1. Click **Start Capture**.
2. Drag a rectangle over the subtitle area on your screen.
3. Press **ESC** to cancel, or release the mouse to confirm.
4. Click **Yes** on the confirmation dialog.
5. Recording begins – new text appears in `output/{timestamp}.txt`.
6. Click **Stop Capture** to end the session.

---

## Usage

### Command-line flags

| Flag | Description |
|------|-------------|
| *(none)* | Runs with debug mode on (default). |
| `--no-debug` | Disables saving debug screenshots. Logs are still written. |

### Debug mode

When debug mode is **enabled** (the default):

- Every captured frame is saved to `debug/frame_0001.png`, `debug/frame_0002.png`, …
- The logger outputs at `DEBUG` level to both console and `logs/app.log`.

Use `--no-debug` to suppress image saving when you are satisfied that OCR is working correctly.

### Output

Captured text is written to `output/{YYYYMMDD_HHmmss}.txt`, one new line per
OCR cycle. Each line contains only subtitle text that has **not** been seen
before in the current session.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    main.py (GUI)                     │
│  ┌──────────┐   ┌──────────┐   ┌──────────────────┐ │
│  │ Start /  │   │  Status  │   │  Counter display │ │
│  │ Stop btn │   │  label   │   │  (live stats)    │ │
│  └────┬─────┘   └──────────┘   └──────────────────┘ │
└───────┼──────────────────────────────────────────────┘
        │
        ▼
┌───────────────────┐     ┌──────────────────┐
│  screen_capture   │────▶│   ocr_engine     │
│  .AreaSelector    │     │  (RapidOCR)      │
│  .ScreenCapturer  │     │  ch + en model   │
│  (mss backend)    │     └────────┬─────────┘
└───────────────────┘              │
                                   ▼
                          ┌──────────────────┐
                          │   text_dedup     │
                          │  rolling window  │
                          │  + line tracking │
                          └────────┬─────────┘
                                   │
                                   ▼
                          ┌──────────────────┐
                          │  output/*.txt    │
                          │  (new lines only)│
                          └──────────────────┘
```

### Component overview

| Module | Responsibility |
|--------|---------------|
| `main.py` | tkinter GUI, orchestrates the capture → OCR → dedup → write pipeline. |
| `screen_capture.py` | `AreaSelector` – fullscreen overlay for region selection. `ScreenCapturer` – threaded region capture with `mss`. |
| `ocr_engine.py` | Wraps `rapidocr-onnxruntime`; provides `recognize()` and `recognize_text_only()`. |
| `text_dedup.py` | Rolling-window fuzzy comparison + global seen-line set. |
| `config.py` | Single source of truth for all tunable parameters. |
| `logger_setup.py` | Rotating-file + console logger. |

### Deduplication algorithm

1. Raw text is **cleaned** (strip, dedup lines within the same frame).
2. If it matches the **last appended text exactly**, it is skipped.
3. A **fuzzy ratio** (`difflib.SequenceMatcher`) is computed against the last *N* results. If `ratio > threshold` (default 0.85), only lines not found in the global **seen set** are returned.
4. New lines are added to the seen set and written to the output file.

This handles both exact duplicates (same subtitle frame captured twice)
and near-duplicates (scrolling text where most lines overlap).

---

## Configuration

Edit `config.py` → class `AppConfig`:

| Setting | Default | Description |
|---------|---------|-------------|
| `CAPTURE_INTERVAL_SEC` | `1.0` | Seconds between capture/OCR cycles. |
| `DEDUP_WINDOW_SIZE` | `10` | How many recent OCR results to keep for fuzzy comparison. |
| `DEDUP_SIMILARITY_THRESHOLD` | `0.85` | Similarity ratio above which text is considered a near-duplicate. |
| `DEBUG_MODE` | `True` | Save every frame to `debug/` and log at DEBUG level. |
| `SELECTION_BORDER_COLOR` | `"red"` | Color of the drag rectangle on the overlay. |

---

## Project structure

```
text-screen-append-txt/
├── main.py              # Entry point
├── config.py            # Configuration
├── logger_setup.py      # Logging
├── screen_capture.py    # Area selection + capture loop
├── ocr_engine.py        # RapidOCR wrapper
├── text_dedup.py        # Deduplication
├── __init__.py          # Package init
├── requirements.txt
├── README.md
├── AGENTS.md            # AI-agent-friendly reference
├── docs/
│   └── architecture.md  # Detailed architecture documentation
├── output/              # Generated .txt files (gitignored)
├── debug/               # Debug screenshots (gitignored)
└── logs/                # Log files (gitignored)
```

---

## FAQ

**Q: Why RapidOCR instead of Tesseract?**

RapidOCR (ONNX-based) offers significantly better accuracy on mixed Chinese +
English screen text, runs entirely offline, and has a small model footprint
(~50 MB).

**Q: The OCR is slow / uses too much CPU.**

Reduce the capture frequency by editing `CAPTURE_INTERVAL_SEC` in
`config.py`.  The default of 1.0 s is a good balance for subtitle capture.

**Q: Text is being duplicated in the output.**

The dedup threshold is conservative by default.  If you see unwanted
duplicates, lower `DEDUP_SIMILARITY_THRESHOLD` (e.g., to `0.80`) or
increase `DEDUP_WINDOW_SIZE`.

**Q: How do I change the OCR language?**

RapidOCR's default Chinese model already covers simplified Chinese,
traditional Chinese, and English/Latin characters.  For other languages,
refer to the [RapidOCR documentation](https://github.com/RapidAI/RapidOCR).

---

## License

This project is licensed under the MIT License.
