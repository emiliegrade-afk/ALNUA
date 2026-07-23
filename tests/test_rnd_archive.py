"""Archive R&D proposals — JSON + anti-resurrection on sync."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from services.rnd_repository import RndRepository


@pytest.fixture
def json_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> RndRepository:
    ideas_file = tmp_path / "rnd_ideas.json"
    monkeypatch.setattr("services.rnd_repository.RND_IDEAS_FILE", ideas_file)
    repo = RndRepository(db=MagicMock())
    repo._use_db = False
    return repo


def test_archive_idea_marks_json_and_stays_archived_on_sync(json_repo: RndRepository) -> None:
    idea = {
        "id": "idea_test_1",
        "title": "Test idea",
        "description": "Desc",
        "lifecycle_status": "raw",
    }
    json_repo._save_json_ideas([idea])

    assert json_repo.archive_idea("idea_test_1") is True

    stored = json_repo._load_json_ideas()
    assert stored[0]["lifecycle_status"] == "archived"
    assert json_repo.get_top_ideas(inbox_only=True) == []

    # Simulate stale JSON after a cycle — sync must not resurrect.
    json_repo._use_db = True
    json_repo.db.select.return_value = [
        {"id": "uuid-1", "legacy_id": "idea_test_1", "lifecycle_status": "archived"}
    ]
    json_repo.db.update.return_value = {
        "id": "uuid-1",
        "legacy_id": "idea_test_1",
        "lifecycle_status": "archived",
    }
    stale = {"id": "idea_test_1", "title": "Test idea", "description": "Desc", "lifecycle_status": "raw"}
    json_repo.sync_idea_to_db(stale)
    update_payload = json_repo.db.update.call_args[0][2]
    assert update_payload["lifecycle_status"] == "archived"


def test_archive_idea_rejects_promoted(json_repo: RndRepository) -> None:
    json_repo._save_json_ideas(
        [
            {
                "id": "idea_promoted",
                "title": "Has dossier",
                "dossier_id": "dossier-uuid",
                "lifecycle_status": "dossier_draft",
            }
        ]
    )
    with pytest.raises(ValueError, match="dossier"):
        json_repo.archive_idea("idea_promoted")
