"""Tests for R&D committee phase 3."""
from __future__ import annotations

import logging
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("RND_DOSSIER_USE_LLM", "false")

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

from agents.rnd_committee_agent import RndCommitteeAgent  # noqa: E402
from services.rnd_committee import build_committee_team  # noqa: E402
from services.rnd_repository import get_rnd_repository  # noqa: E402


def test_team_builder() -> None:
    saas = build_committee_team("saas")
    ids = {m["id"] for m in saas}
    assert "pm" in ids and "marketing" in ids and "dev_app" in ids
    hw = build_committee_team("hardware")
    assert "hardware" in {m["id"] for m in hw}
    print("OK team builder")


def test_committee_flow() -> None:
    repo = get_rnd_repository()
    if not repo._use_db:
        print("SKIP committee — Supabase unavailable")
        return

    legacy_id = f"test_committee_{uuid.uuid4().hex[:8]}"
    test_idea = {
        "id": legacy_id,
        "title": "Test Committee Phase 3",
        "description": "Validation comité multi-agents",
        "domain": "saas",
        "effort": "S",
        "source": "test_script",
        "status": "evaluated",
        "score": 20,
        "verdict": "MAYBE",
        "agent_reasoning": "Test phase 3",
        "lifecycle_status": "raw",
    }
    json_ideas = repo._load_json_ideas()
    json_ideas.append(test_idea)
    repo._save_json_ideas(json_ideas)
    repo.sync_idea_to_db(test_idea)

    agent = RndCommitteeAgent()
    try:
        dossier, _ = repo.promote_idea_to_dossier(legacy_id, actor="test_script")
        started = agent.start_session(str(dossier.id), actor="test_script")
        assert started["session"]["status"] == "active"
        assert len(started["messages"]) >= 1

        posted = agent.post_message(
            str(dossier.id),
            started["session"]["session_id"],
            "Est-ce que le pricing est réaliste ?",
            actor="test_script",
        )
        assert posted["user_message"]["role"] == "user"

        closed = agent.close_session(
            str(dossier.id),
            started["session"]["session_id"],
            apply_sections=False,
            actor="test_script",
        )
        assert closed["session"]["status"] == "closed"
        print("OK committee start/message/close")
    finally:
        db_row = repo.get_idea_db_row(legacy_id)
        if db_row and db_row.get("dossier_id"):
            did = str(db_row["dossier_id"])
            for table in (
                "rnd_committee_messages",
                "rnd_committee_sessions",
                "rnd_dossier_events",
                "rnd_dossier_sections",
            ):
                try:
                    for row in repo.db.select(table, filters={"dossier_id": did}):
                        repo.db.delete(table, row["id"])
                except Exception:
                    pass
            try:
                for row in repo.db.select(
                    "rnd_committee_messages",
                    filters={"session_id": "committee_%"},
                ):
                    pass
            except Exception:
                pass
            repo.db.delete("rnd_dossiers", did)
            repo.db.update("rnd_ideas", db_row["id"], {"dossier_id": None, "lifecycle_status": "raw"})
        json_ideas = [i for i in repo._load_json_ideas() if i.get("id") != legacy_id]
        repo._save_json_ideas(json_ideas)
        print("OK cleanup committee test")


def main() -> int:
    try:
        test_team_builder()
        test_committee_flow()
        print("\n=== Phase 3 committee tests passed ===")
        return 0
    except Exception as exc:
        logging.exception("Test failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
