"""OCR end-to-end test: image -> Audiveris -> MusicXML -> MIDI -> jianpu -> PNG.

Dependencies:
    - Audiveris 5.x (this machine: D:\\Program Files (x86)\\Audiveris\\Audiveris.exe)
    - MuseScore 4 CLI
    - Source MusicXML: data/output_demo/bach_prelude_m1_m4.musicxml (produced by complex_e2e.py)

Tests are skipped if Audiveris or MuseScore is unavailable.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.music_convert import core  # noqa: F401  (kept for future direct use)
from src.ocr import AudiverisConfig, find_audiveris, image_to_musicxml, is_audiveris_available
from src.render import find_musescore


PROJECT_TEST_INPUT = ROOT / "data" / "test_input"


def _ensure_test_image(tmp: Path) -> Path:
    """Render bach_prelude_m1_m4.musicxml into a PNG via MuseScore for use as OMR input."""
    src_xml = ROOT / "data" / "output_demo" / "bach_prelude_m1_m4.musicxml"
    if not src_xml.exists():
        raise FileNotFoundError(
            f"Need {src_xml} first; run complex_e2e.py to generate it."
        )
    mscore = find_musescore()
    if not mscore:
        raise RuntimeError("MuseScore 4 is required to generate the test image")

    target = tmp / "test_input.png"
    PROJECT_TEST_INPUT.mkdir(parents=True, exist_ok=True)
    # Render directly into tmp to avoid polluting data/test_input.
    cmd = [mscore, "-r", "200", "-o", str(target), str(src_xml)]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
    # MuseScore 4 names the PNG ``<target_stem>-1.png``; rename it.
    actual = target.with_name(target.stem + "-1.png")
    if actual.exists() and not target.exists():
        actual.rename(target)
    if not target.exists():
        raise RuntimeError(f"Failed to generate test image: {target}")
    return target


def test_ocr_e2e(tmp: Path) -> None:
    """Full OCR pipeline: image -> Audiveris -> MusicXML -> MIDI -> jianpu -> PNG."""
    if not is_audiveris_available():
        print("  [skip] Audiveris unavailable, skipping OCR E2E")
        return
    print("  Audiveris:", find_audiveris())
    print("  MuseScore:", find_musescore())

    img = _ensure_test_image(tmp)
    print(f"  Test image: {img} ({img.stat().st_size} bytes)")

    from src.main import run_pipeline
    results = run_pipeline(
        input_path=img,
        out_dir=tmp / "out",
        bpm=100,
        render_png=True,
        skip_ocr=False,
    )
    assert len(results) == 1
    r = results[0]
    assert r.musicxml and r.musicxml.exists()
    assert r.midi and r.midi.exists() and r.midi.stat().st_size > 0
    assert r.jianpu_txt and r.jianpu_txt.exists()
    assert r.rendered_png and r.rendered_png.exists() and r.rendered_png.stat().st_size > 1024

    jianpu = r.jianpu_txt.read_text(encoding="utf-8")
    assert any(c.isdigit() for c in jianpu), f"OCR jianpu contains no digits: {jianpu!r}"
    print(f"  MusicXML: {r.musicxml.name} ({r.musicxml.stat().st_size} bytes)")
    print(f"  MIDI    : {r.midi.name} ({r.midi.stat().st_size} bytes)")
    print(f"  jianpu  : {jianpu[:80]!r}")
    print(f"  PNG     : {r.rendered_png.name} ({r.rendered_png.stat().st_size} bytes)")


def _ensure_test_pdf(tmp: Path) -> Path:
    """Render bach_prelude_m1_m4.musicxml into a PDF via MuseScore for use as OMR input."""
    src_xml = ROOT / "data" / "output_demo" / "bach_prelude_m1_m4.musicxml"
    if not src_xml.exists():
        raise FileNotFoundError(f"Need {src_xml} first")
    mscore = find_musescore()
    if not mscore:
        raise RuntimeError("MuseScore 4 is required to generate the test PDF")
    target = tmp / "test_input.pdf"
    cmd = [mscore, "-o", str(target), str(src_xml)]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=60)
    if not target.exists():
        raise RuntimeError(f"Failed to generate test PDF: {target}")
    return target


def test_ocr_pdf_e2e(tmp: Path) -> None:
    """Full OCR pipeline with PDF input: PDF -> image -> Audiveris -> MusicXML -> MIDI -> jianpu -> PNG."""
    if not is_audiveris_available():
        print("  [skip] Audiveris unavailable, skipping PDF OCR E2E")
        return
    pdf = _ensure_test_pdf(tmp)
    print(f"  Test PDF: {pdf} ({pdf.stat().st_size} bytes)")

    from src.main import run_pipeline
    results = run_pipeline(
        input_path=pdf,
        out_dir=tmp / "out_pdf",
        bpm=100,
        render_png=True,
        skip_ocr=False,
    )
    assert len(results) == 1
    r = results[0]
    assert r.musicxml and r.musicxml.exists()
    assert r.midi and r.midi.exists()
    assert r.jianpu_txt and r.jianpu_txt.exists()
    jianpu = r.jianpu_txt.read_text(encoding="utf-8")
    assert any(c.isdigit() for c in jianpu)
    print(f"  PDF -> MusicXML: {r.musicxml.name}")
    print(f"  PDF -> MIDI    : {r.midi.name}")
    print(f"  PDF -> jianpu  : {jianpu[:80]!r}")
    if r.rendered_png:
        print(f"  PDF -> PNG     : {r.rendered_png.name} ({r.rendered_png.stat().st_size} bytes)")


def test_ocr_handles_unavailable(tmp: Path) -> None:
    """When Audiveris is missing, raise a clear RuntimeError instead of crashing."""
    # Force the resolver to look at a nonexistent path via the environment variable.
    old = os.environ.get("AUDIVERIS_EXE")
    os.environ["AUDIVERIS_EXE"] = r"Z:\nonexistent\audiveris.exe"
    try:
        try:
            image_to_musicxml(tmp / "nope.png", tmp, AudiverisConfig())
            raised = False
        except RuntimeError as e:
            raised = True
            assert "Audiveris" in str(e)
        assert raised, "Missing Audiveris should raise RuntimeError"
    finally:
        if old is None:
            os.environ.pop("AUDIVERIS_EXE", None)
        else:
            os.environ["AUDIVERIS_EXE"] = old


def main() -> int:
    print("=== OCR end-to-end test ===")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        print("\n[1] Full OCR pipeline (PNG input):")
        test_ocr_e2e(tmp)
        print("\n[2] Full OCR pipeline (PDF input):")
        test_ocr_pdf_e2e(tmp)
        print("\n[3] Audiveris unavailable -> clear error:")
        test_ocr_handles_unavailable(tmp)
    print("\nALL OCR E2E PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
