"""MusicXML <-> MIDI <-> numbered-notation (jianpu) core conversion.

Dependencies:
    - music21  : MusicXML parsing/writing; numbered-notation rendering
    - pretty_midi: MIDI file parsing/writing

The numbered (jianpu) text follows music21's numbered notation, where C4 = 1,
D4 = 2, etc., and the output is a space-separated string of the form
``4/4 C4 D4 E4 F4 | G4 G4 G4 G4 |`` suitable for direct inspection or display.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import music21
import pretty_midi


@dataclass
class ConvertOptions:
    """Common conversion options."""

    bpm: int = 90
    title: Optional[str] = None
    composer: Optional[str] = None


# ---------- MusicXML <-> MIDI ----------

def musicxml_to_midi(xml_path: str | Path, midi_path: str | Path,
                     options: ConvertOptions | None = None) -> Path:
    """Convert a MusicXML file to a MIDI file.

    Args:
        xml_path: input MusicXML path (.xml / .musicxml)
        midi_path: output MIDI path (.mid / .midi)
        options: conversion options (reserved; not deeply used yet)

    Returns:
        The path of the MIDI file actually written.
    """
    xml_path = Path(xml_path)
    midi_path = Path(midi_path)
    midi_path.parent.mkdir(parents=True, exist_ok=True)

    score = music21.converter.parse(str(xml_path))
    # music21 has a built-in MIDI writer.
    score.write("midi", fp=str(midi_path))
    return midi_path


def midi_to_musicxml(midi_path: str | Path, xml_path: str | Path,
                     options: ConvertOptions | None = None) -> Path:
    """Convert a MIDI file to a MusicXML file.

    music21's MIDI parser reconstructs a best-effort part/measure structure.
    """
    midi_path = Path(midi_path)
    xml_path = Path(xml_path)
    xml_path.parent.mkdir(parents=True, exist_ok=True)

    score = music21.converter.parse(str(midi_path))
    score.write("musicxml", fp=str(xml_path))
    return xml_path


# ---------- Numbered notation (jianpu) ----------

def musicxml_to_jianpu_text(xml_path: str | Path) -> str:
    """Extract numbered-notation (jianpu) text from a MusicXML file.

    Uses music21's ``recurse()`` to walk every note, mapping pitches to
    jianpu numerals as follows:
        1 = do, 2 = re, 3 = mi, 4 = fa, 5 = sol, 6 = la, 7 = ti
    Accidentals are written as ``#`` / ``b`` prefixes.
    """
    score = music21.converter.parse(str(xml_path))
    parts = []
    for element in score.recurse().notes:
        if isinstance(element, music21.chord.Chord):
            parts.append("/".join(_pitch_to_jianpu(p) for p in element.pitches))
        else:  # Note
            parts.append(_pitch_to_jianpu(element.pitch))
    return " ".join(parts)


def jianpu_text_to_midi(jianpu: str, midi_path: str | Path,
                        options: ConvertOptions | None = None) -> Path:
    """Minimal jianpu-text -> MIDI converter.

    Accepted jianpu tokens:
        1 2 3 4 5 6 7   ->  C D E F G A B (starting from middle C)
        # / b           ->  sharp / flat prefix
        |               ->  bar separator (ignored; kept for readability)
        whitespace      ->  token separator

    Missing durations default to one quarter-note beat; tempo is taken from
    ``options.bpm``.
    """
    options = options or ConvertOptions()
    midi_path = Path(midi_path)
    midi_path.parent.mkdir(parents=True, exist_ok=True)

    pm = pretty_midi.PrettyMIDI(initial_tempo=options.bpm)
    inst = pretty_midi.Instrument(program=0)  # Acoustic Grand Piano
    time = 0.0
    beat = 60.0 / options.bpm  # one beat (seconds)
    token = ""
    for ch in jianpu:
        if ch in " \n\t|":
            _emit(token, time, beat, inst)
            time += beat
            token = ""
        else:
            token += ch
    _emit(token, time, beat, inst)
    if token:
        time += beat

    pm.instruments.append(inst)
    pm.write(str(midi_path))
    return midi_path


def jianpu_text_to_musicxml(jianpu: str, xml_path: str | Path,
                            options: ConvertOptions | None = None) -> Path:
    """jianpu text -> MusicXML: jianpu -> MIDI -> MusicXML."""
    options = options or ConvertOptions()
    tmp_midi = Path(xml_path).with_suffix(".tmp.mid")
    jianpu_text_to_midi(jianpu, tmp_midi, options)
    try:
        return midi_to_musicxml(tmp_midi, xml_path, options)
    finally:
        if tmp_midi.exists():
            tmp_midi.unlink()


# ---------- Internal helpers ----------

_PITCH_INDEX = {"C": 0, "D": 1, "E": 2, "F": 3, "G": 4, "A": 5, "B": 6}


def _pitch_to_jianpu(p: music21.pitch.Pitch) -> str:
    """Convert a single pitch to its jianpu numeral.

    Jianpu octaves differ from staff notation: middle C is ``1`` and each
    ascending octave adds ``+`` to the numeral.
    """
    semitone = p.midi  # 60 = C4
    # C4 -> 1, D4 -> 2, ... B4 -> 7, C5 -> 1 (next octave)
    degree = (semitone - 60) % 12
    degree_to_num = {0: 1, 2: 2, 4: 3, 5: 4, 7: 5, 9: 6, 11: 7}
    accidental = ""
    if degree in (1, 3, 6, 8, 10):  # black key
        # In jianpu, a sharp on a white-key slot is written as 1#/2#/4#/5#/6#.
        white_key_offset = {1: 0, 3: 1, 6: 3, 8: 4, 10: 5}
        base_semitone = semitone - 1
        accidental = "#"
        if semitone % 12 == 1:  # C#/Db -> prefer the Db spelling
            base_semitone = semitone + 1
            accidental = "b"
    else:
        base_semitone = semitone
    octave = (base_semitone - 60) // 12
    base_semitone_in_octave = (base_semitone - 60) % 12
    num = degree_to_num[base_semitone_in_octave]
    # Higher/lower octaves: dots above/below. music21 uses ``+``/``-`` here
    # as a compact notation.
    suffix = ""
    if octave > 0:
        suffix = "+" * octave
    elif octave < 0:
        suffix = "-" * (-octave)
    return f"{accidental}{num}{suffix}"


def _emit(token: str, time: float, beat: float, inst: pretty_midi.Instrument) -> None:
    """Parse a single jianpu token and append a note."""
    if not token:
        return
    accidental = ""
    num_part = token
    if token and token[0] in "#b":
        accidental = token[0]
        num_part = token[1:]
    if not num_part or not num_part[0].isdigit():
        return
    digits = ""
    suffix = ""
    for c in num_part:
        if c.isdigit():
            digits += c
        else:
            suffix += c
    if not digits:
        return
    octave_offset = 0
    if "+" in suffix:
        octave_offset = suffix.count("+")
    if "-" in suffix:
        octave_offset = -suffix.count("-")
    # numeral -> semitone offset within an octave
    num_to_degree = {"1": 0, "2": 2, "3": 4, "4": 5, "5": 7, "6": 9, "7": 11}
    semitone = 60 + octave_offset * 12 + num_to_degree[digits[0]]
    if accidental == "#":
        semitone += 1
    elif accidental == "b":
        semitone -= 1
    note = pretty_midi.Note(velocity=80, pitch=semitone, start=time, end=time + beat)
    inst.notes.append(note)
