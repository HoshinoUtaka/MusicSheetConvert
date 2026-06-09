# Contributing

Thanks for your interest in contributing to **MusicSheetConvert**! This document
covers the basics of how to set up a development environment, run the test
suite, and submit changes.

## Development Setup

The project ships with helper scripts that create a dedicated Python venv and
install all dependencies:

```bash
# Windows (cmd / PowerShell)
scripts\install.bat

# Unix / Git Bash
./scripts/install.sh
```

## External Dependencies

| Tool | Required for |
|------|--------------|
| Audiveris 5.x | OMR (image/PDF -> MusicXML) |
| MuseScore 4   | Staff-notation rendering (PNG / PDF) |
| Poppler       | `pdf2image` (PDF -> image) |

Override locations via the `AUDIVERIS_EXE`, `MUSESCORE_EXE`, and `PATH`
environment variables respectively. The `find_audiveris()` and
`find_musescore()` helpers perform the auto-discovery.

## Running Tests

```bash
python tests/smoke.py            # MusicXML <-> MIDI <-> jianpu
python tests/e2e_cli.py          # end-to-end pipeline (skip OCR)
python tests/complex_e2e.py      # grand staff, key signatures, chords, Bach prelude
python tests/ocr_e2e.py          # real Audiveris + MuseScore pipeline
```

Tests skip gracefully when an external dependency is missing.

## Code Style

- PEP 8, 4-space indent, type hints encouraged.
- All comments, docstrings, log messages, and CLI help text are in **English**.
- Module structure mirrors responsibility: `core.py` for pure-Python
  conversion, `advanced.py` for score builders, `ocr/`, `preprocess/`, `render/`
  for their respective adapters.

## Submitting Changes

1. Fork the repository and create a feature branch.
2. Run the full test suite locally and make sure it passes.
3. Keep commits focused and the history clean.
4. Open a pull request describing the motivation and approach.

Bug reports and feature requests are welcome via GitHub Issues.
