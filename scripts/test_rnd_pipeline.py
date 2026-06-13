"""Tests for R&D pipeline status (phase 8)."""
from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("RND_DOSSIER_USE_LLM", "false")

from services.rnd_pipeline import build_dossier_pipeline, rnd_module_health  # noqa: E402
from services.rnd_repository import get_rnd_repository  # noqa: E402
from services.rnd_schemas import RndDossierOut, RndDossierSectionOut  # noqa: E402


def test_module_health() -> None:
    repo = get_rnd_repository()
    health = rnd_module_health(repo.db)
    assert health["module"] == "rnd_dossier"
    assert health["checks"]["rnd_dossiers"]["ok"] is True
    print(f"OK rnd health — {health['status']}")


def test_pipeline_stages() -> None:
    did = str(uuid.uuid4())
    dossier = RndDossierOut(
        id=did,
        idea_id=str(uuid.uuid4()),
        slug="pipeline-test",
        title="Pipeline Test",
        domain="saas",
        branch="app",
        status="ready_for_ceo",
        ceo_status="pending",
        finance_json={"verdict_finance": "viable"},
        committee_report_md="## CR\nGO",
        sections=[
            RndDossierSectionOut(
                id=str(uuid.uuid4()),
                dossier_id=did,
                section_key="problem",
                title="P",
                content_md="x" * 30,
                status="validated",
            )
        ],
        sections_validated_count=1,
        sections_total_count=8,
    )
    pipeline = build_dossier_pipeline(dossier)
    assert pipeline["stages_total"] == 7
    assert pipeline["progress_pct"] > 0
    assert any(s["id"] == "social" and s["status"] == "locked" for s in pipeline["stages"])
    assert pipeline["next_action"]
    print(f"OK pipeline — {pipeline['progress_pct']}% next={pipeline['next_tab']}")


if __name__ == "__main__":
    test_module_health()
    test_pipeline_stages()
    print("\nPipeline tests passed.")
