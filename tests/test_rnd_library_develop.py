"""Library → R&D development pipeline."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from agents import rnd_center


@pytest.fixture
def rnd_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    ideas_file = tmp_path / "rnd_ideas.json"
    monkeypatch.setattr(rnd_center, "RND_IDEAS_FILE", ideas_file)
    return ideas_file


def test_develop_idea_from_library_scores_and_saves(rnd_file: Path) -> None:
  expanded = {
      "title": "NomadComply Plus",
      "domain": "saas",
      "description": "Compliance assistant for nomads.",
      "why_now": "Regulation complexity in 2026.",
      "effort": "M",
  }
  evaluated = {
      **expanded,
      "score": 24,
      "market_score": 8,
      "feasibility_score": 8,
      "vision_score": 8,
      "verdict": "GO",
      "reasoning": "Strong fit.",
      "next_step": "MVP",
      "status": "evaluated",
  }

  with (
      patch.object(rnd_center, "get_vision", return_value="Vision test"),
      patch.object(rnd_center, "_expand_library_concept", return_value=expanded),
      patch.object(rnd_center, "_evaluate_idea", return_value=evaluated),
      patch.object(rnd_center, "_prototype_idea", return_value="/tmp/spec.md"),
  ):
      result = rnd_center.develop_idea_from_library(
          title="NomadComply",
          summary="Fiche bibliothèque sur la compliance nomade.",
          library_entry_id="entry-uuid-1",
          source="bibliothèque recherche",
          prototype_if_go=True,
      )

  assert result["score"] == 24
  assert result["verdict"] == "GO"
  assert result["status"] == "prototyped"
  assert result["library_entry_id"] == "entry-uuid-1"

  saved = rnd_center._load_ideas()
  assert len(saved) == 1
  assert saved[0]["id"] == result["id"]

  # Second call with same library entry should not duplicate when already scored.
  with patch.object(rnd_center, "_load_ideas", return_value=saved):
      again = rnd_center.develop_idea_from_library(
          title="NomadComply",
          summary="Fiche bibliothèque",
          library_entry_id="entry-uuid-1",
      )
  assert again["id"] == result["id"]


def test_develop_pending_library_ideas_upgrades_shallow_inject(rnd_file: Path) -> None:
  shallow = {
      "id": "idea_old_lib",
      "title": "Idée bibliothèque brute",
      "description": "Juste le texte du rapport CEO",
      "source": "bibliothèque CEO",
      "status": "pending_evaluation",
      "score": None,
  }
  rnd_center._save_ideas([shallow])

  evaluated = {
      **shallow,
      "domain": "ia",
      "why_now": "now",
      "effort": "S",
      "score": 22,
      "verdict": "GO",
      "reasoning": "ok",
      "status": "evaluated",
  }

  with (
      patch.object(rnd_center, "get_vision", return_value="Vision"),
      patch.object(rnd_center, "_expand_library_concept", return_value=evaluated),
      patch.object(rnd_center, "_evaluate_idea", return_value=evaluated),
      patch.object(rnd_center, "_prototype_idea", return_value=""),
  ):
      developed = rnd_center.develop_pending_library_ideas(limit=1)

  assert len(developed) == 1
  assert developed[0]["id"] == "idea_old_lib"
  assert developed[0]["score"] == 22
