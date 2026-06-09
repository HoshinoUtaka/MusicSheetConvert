# Architecture

## Data Flow

```
PDF/Image ──(preprocess)──> PNG  ──(Audiveris OMR)──> MusicXML/.mxl
                                                       │
                                                       ├─(music21)──> MIDI/.mid
                                                       ├─(jianpu)───> jianpu/.txt
                                                       └─(MuseScore)─> staff PNG
```

## Module Boundaries

- `src/main.py`                 : CLI + pipeline orchestration; contains no conversion logic itself.
- `src/music_convert/core.py`   : Pure-Python conversion; only depends on `music21` / `pretty_midi`.
- `src/music_convert/advanced.py`: Builders for complex scores (grand staff, key signatures, chords, Bach prelude).
- `src/ocr/__init__.py`         : Wraps the external OMR engine (Audiveris); raises clear errors on failure.
- `src/preprocess/__init__.py`  : OpenCV image processing and `pdf2image` conversion.
- `src/render/__init__.py`      : Output layer: jianpu text and MuseScore-based rendering.

## Extension Points

| Need | Where to change |
|------|-----------------|
| Swap the OMR engine | `src/ocr/__init__.py`: add a new engine alongside Audiveris. |
| Refine jianpu duration handling | `core._emit`: extend the token grammar (e.g. `1-`, `1.`, `1_`). |
| Web UI | Add an `app.py` at the project root that calls `run_pipeline` and exposes FastAPI/Flask endpoints. |
| Self-trained jianpu OCR | Add `src/ocr/jianpu_ocr.py` that loads a Keras / PyTorch model. |
| Additional demos | Add a new function in `src/music_convert/advanced.py` and wire it into `src/main.py:run_demo`. |
