# Changelog

All notable changes to **MusicSheetConvert** are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- End-to-end OCR pipeline: image / PDF -> Audiveris -> MusicXML -> MIDI -> jianpu / staff PNG.
- Built-in complex-score generators: grand staff (two hands), 9 key-signature
  demonstrations, ii-V-I 7th-chord progression, Bach Prelude in C major (m1..m4).
- Render-to-file helpers via MuseScore 4: PNG, PDF, SVG.
- Test suite: `smoke`, `e2e_cli`, `complex_e2e`, `ocr_e2e`.

### Changed
- All user-facing strings, docstrings, log messages, CLI help, and the README
  rewritten in English.

## [0.1.0] - 2026-06-09

### Added
- Initial release: MusicXML <-> MIDI <-> jianpu-text core conversions.
- OpenCV-based image preprocessing and `pdf2image` PDF rasterization.
- Audiveris 5.x adapter for OMR (image / PDF -> MusicXML).
- MuseScore 4 adapter for staff-notation rendering.
