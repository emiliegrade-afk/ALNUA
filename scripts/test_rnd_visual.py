"""Tests for R&D visual assets (phase 4)."""
from __future__ import annotations

import logging
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

os.environ.setdefault("RND_DOSSIER_USE_LLM", "false")

from agents.rnd_visual_agent import RndVisualAgent  # noqa: E402
from services.rnd_repository import get_rnd_repository  # noqa: E402
from services.rnd_schemas import RndDossierOut, RndDossierSectionOut  # noqa: E402
from services.rnd_visual_generator import ASSET_SPECS, generate_dossier_assets  # noqa: E402


def _fake_dossier() -> RndDossierOut:
    slug = f"test-visual-{uuid.uuid4().hex[:8]}"
    sections = [
        RndDossierSectionOut(
            id=str(uuid.uuid4()),
            dossier_id="x",
            section_key=k,
            title=k,
            content_md=f"Content for {k} — ALNUA test dossier with enough text.",
            status="draft",
            sort_order=i,
        )
        for i, k in enumerate(["problem", "solution", "mvp", "business_case"], start=1)
    ]
    return RndDossierOut(
        id=str(uuid.uuid4()),
        slug=slug,
        title="Visual Test Project",
        domain="app",
        branch="app",
        status="partial_validated",
        ceo_status="pending",
        idea_id=str(uuid.uuid4()),
        sections=sections,
        finance_json={
            "capex_eur": 800,
            "opex_monthly_eur": 120,
            "revenue_hypothesis": {"m12_monthly_run_rate_eur": 2500},
        },
        sections_validated_count=2,
        sections_total_count=4,
    )


def test_pillow_render_local() -> None:
    dossier = _fake_dossier()
    out_dir = Path("data/rnd_dossiers") / dossier.slug / "assets"
    rows = generate_dossier_assets(dossier, output_dir=out_dir, force=True)
    expected = len([s for s in ASSET_SPECS if not s.get("requires_finance") or dossier.finance_json])
    assert len(rows) == expected, f"expected {expected} assets, got {len(rows)}"
    for row in rows:
        path = Path(row["file_path"])
        if not path.is_absolute():
            path = Path(os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")) / row["file_path"]
        assert path.is_file(), f"missing file {path}"
    print(f"OK pillow render — {len(rows)} PNG files in {out_dir}")


def test_visual_agent_list() -> None:
    repo = get_rnd_repository()
    items = repo.list_dossiers(limit=1)
    if not items:
        print("SKIP visual agent — no dossiers in DB")
        return
    agent = RndVisualAgent()
    assets = agent.list_assets(items[0].id)
    print(f"OK list_assets — dossier={items[0].slug} count={len(assets)}")


def test_visual_agent_generate_db() -> None:
    repo = get_rnd_repository()
    items = repo.list_dossiers(limit=1)
    if not items:
        print("SKIP generate — no dossiers in DB")
        return
    dossier_id = items[0].id
    agent = RndVisualAgent()
    result = agent.generate_assets(dossier_id, force=True)
    assert result["dossier_id"] == dossier_id
    assert result["created"] >= 1
    assert len(result["assets"]) >= 1
    print(f"OK generate_assets — created={result['created']} total={len(result['assets'])}")


if __name__ == "__main__":
    test_pillow_render_local()
    test_visual_agent_list()
    test_visual_agent_generate_db()
    print("\nAll visual tests passed.")
