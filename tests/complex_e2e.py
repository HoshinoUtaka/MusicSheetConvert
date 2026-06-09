"""Complex-score E2E test: grand staff (two hands) / multiple key signatures / chords
all go through MusicXML/MIDI/jianpu/PNG.

Dependencies:
    - music21, pretty_midi (always)
    - MuseScore 4 CLI (for PNG rendering and round-trip tests)
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.music_convert import core
from src.music_convert.advanced import (
    NoteSpec,
    build_bach_prelude_c_major,
    build_chord_progression,
    build_grand_staff,
    build_key_demonstration,
    write_score,
)
from src.render import find_musescore, midi_to_musicxml, musicxml_to_png


def _has_musescore() -> bool:
    return find_musescore() is not None


def test_grand_staff_in_each_key(tmp: Path) -> None:
    """Build a grand-staff score in every key signature, verify MusicXML/MIDI/jianpu are produced."""
    from music21 import pitch as m21pitch
    from src.music_convert.advanced import KEY_PRESETS
    for key_name in KEY_PRESETS.keys():
        tonic = KEY_PRESETS[key_name].tonic
        t = m21pitch.Pitch(tonic.nameWithOctave)
        rh = [[NoteSpec([t.transpose(j).nameWithOctave], 1.0) for j in (0, 2, 4, 5)],
              [NoteSpec([t.transpose(j).nameWithOctave], 1.0) for j in (7, 9, 11, 12)]]
        lh = [[NoteSpec([f"{tonic.name}3"], 4.0)] for _ in range(2)]
        score = build_grand_staff(rh, lh, key_name=key_name,
                                  title=f"Grand Staff in {key_name}")
        paths = write_score(score, tmp / key_name, f"gs_{key_name}")
        assert paths["musicxml"].exists()
        assert paths["midi"].exists() and paths["midi"].stat().st_size > 0

        jianpu = core.musicxml_to_jianpu_text(paths["musicxml"])
        # We can't hard-code 1/2/5 because minor / flat keys may not contain
        # "1" as the tonic; just verify there are enough digits overall.
        nums = re.findall(r"\d", jianpu)
        assert len(nums) >= 4, f"jianpu lacks enough digits: {jianpu}"
        print(f"  {key_name:3} jianpu: {jianpu}")


def test_chord_progression_with_7ths(tmp: Path) -> None:
    """Cmaj7 - Dm7 - G7 - Cmaj7 7th-chord progression."""
    chords = [
        ["C4", "E4", "G4", "B4"],
        ["D4", "F4", "A4", "C5"],
        ["G3", "B3", "D4", "F4"],
        ["C4", "E4", "G4", "B4"],
    ]
    score = build_chord_progression(chords, key_name="C", title="ii-V-I with 7ths")
    paths = write_score(score, tmp / "chord7", "prog")
    jianpu = core.musicxml_to_jianpu_text(paths["musicxml"])
    print(f"  C major ii-V-I 7th chords jianpu: {jianpu}")
    # Should have 4 four-note chords; first one is Cmaj7 -> 1/3/5/7.
    assert jianpu.startswith("1/3/5/7")
    # G7 root is 5.
    assert "5-/7-/2/4" in jianpu


def test_key_demonstration_all_keys(tmp: Path) -> None:
    """Cover all 9 key signatures: C / G / D / F / Bb / Eb / Am / Em / Dm."""
    score = build_key_demonstration()
    paths = write_score(score, tmp / "keys", "demo")
    jianpu = core.musicxml_to_jianpu_text(paths["musicxml"])
    # 9 key signatures x 2 chords = 18 chunks.
    chunks = jianpu.split()
    print(f"  9 key signatures yield {len(chunks)} chunks")
    assert len(chunks) >= 9 * 2  # at least 18


def test_render_png(tmp: Path) -> None:
    """Render a MusicXML to PNG via MuseScore."""
    if not _has_musescore():
        print("  [skip] MuseScore unavailable, skipping PNG render")
        return
    score = build_grand_staff(
        [[NoteSpec(["C4"], 1.0), NoteSpec(["D4"], 1.0),
          NoteSpec(["E4"], 1.0), NoteSpec(["F4"], 1.0)]],
        [[NoteSpec(["C3", "E3", "G3"], 4.0)]],
        key_name="C", title="Render Test"
    )
    paths = write_score(score, tmp / "render", "simple")
    out_png = tmp / "render" / "simple.png"
    musicxml_to_png(paths["musicxml"], out_png)
    assert out_png.exists() and out_png.stat().st_size > 1024
    print(f"  PNG render OK: {out_png.stat().st_size} bytes")


def test_bach_prelude(tmp: Path) -> None:
    """First 4 measures of Bach's Prelude in C major (the classic 8-note broken-chord pattern)."""
    score = build_bach_prelude_c_major()
    paths = write_score(score, tmp / "bach", "prelude_m1_m4")
    jianpu = core.musicxml_to_jianpu_text(paths["musicxml"])
    chunks = jianpu.split()
    print(f"  Bach prelude 4 measures jianpu: {len(chunks)} chunks; first 8: {' '.join(chunks[:8])}")
    # 8 (RH m1) + 8 (RH m2) + 8 (RH m3) + 8 (RH m4) = 32 RH notes
    # + 8 LH notes (2 chunks per measure x 4 measures, one chord each = 8)
    # = 40 chunks total (32 RH + 8 LH)
    assert len(chunks) == 40
    # First note is C5 -> 1+
    assert chunks[0] == "1+"


def test_round_trip_xml_midi_xml(tmp: Path) -> None:
    """MusicXML -> MIDI -> MusicXML roundtrip; verify the note sequence is preserved."""
    if not _has_musescore():
        print("  [skip] MuseScore unavailable, skipping roundtrip")
        return
    score = build_grand_staff(
        [[NoteSpec(["C4"], 1.0), NoteSpec(["D4"], 1.0),
          NoteSpec(["E4"], 1.0), NoteSpec(["F4"], 1.0)]],
        [[NoteSpec(["C3", "E3", "G3"], 4.0)]],
        key_name="C", title="Roundtrip Test",
    )
    paths = write_score(score, tmp / "rt", "rt")
    # MIDI -> MusicXML via MuseScore
    rt_xml = tmp / "rt" / "rt_from_midi.musicxml"
    midi_to_musicxml(paths["midi"], rt_xml)
    assert rt_xml.exists()
    # Compare
    from music21 import converter
    orig = list(converter.parse(str(paths["musicxml"])).recurse().notes)
    back = list(converter.parse(str(rt_xml)).recurse().notes)
    print(f"  Roundtrip: orig={len(orig)} notes, back={len(back)} notes")
    assert len(orig) == len(back)


def main() -> int:
    print("=== Complex-score E2E test ===")
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        print("\n[1] Grand staff in 9 keys:")
        test_grand_staff_in_each_key(tmp)
        print("\n[2] ii-V-I 7th-chord progression:")
        test_chord_progression_with_7ths(tmp)
        print("\n[3] 9-key-signature demonstration:")
        test_key_demonstration_all_keys(tmp)
        print("\n[4] MuseScore PNG render:")
        test_render_png(tmp)
        print("\n[5] Bach C major prelude:")
        test_bach_prelude(tmp)
        print("\n[6] MusicXML -> MIDI -> MusicXML roundtrip:")
        test_round_trip_xml_midi_xml(tmp)
    print("\nALL E2E PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
