"""Tests for Nadia Desktop TTS text cleanup."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "nadia_desktop"))

from core.tts_text import prepare_text_for_speech, split_for_speech  # noqa: E402


def test_prepare_text_strips_markdown_emojis_and_smileys() -> None:
    raw = (
        "**Bonjour Emilie !** 😊\n"
        "- Point 1 : voir [doc](https://alnua.app)\n"
        "C'est super :) … on avance ?"
    )
    out = prepare_text_for_speech(raw)
    assert "😊" not in out
    assert ":)" not in out
    assert "**" not in out
    assert "http" not in out
    assert "…" not in out
    assert "Bonjour Emilie" in out


def test_prepare_text_normalizes_punctuation() -> None:
    raw = "OK!!! ;;; suite : fin..."
    out = prepare_text_for_speech(raw)
    assert "!!!" not in out
    assert ";;;" not in out
    assert "..." not in out


def test_split_for_speech_returns_short_chunks() -> None:
    raw = (
        "Première phrase avec un peu de contexte pour la journée. "
        "Deuxième phrase qui décrit la suite des actions à mener ce matin. "
        "Troisième phrase pour clore le point."
    )
    chunks = split_for_speech(raw)
    assert chunks
    assert all(len(c) <= 220 for c in chunks)
    assert "Première phrase" in chunks[0]
