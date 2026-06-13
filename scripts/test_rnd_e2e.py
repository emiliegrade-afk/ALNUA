"""Full R&D pipeline E2E (phase 8) — idea to published product page without LLM."""
from __future__ import annotations

import logging
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

os.environ.setdefault("RND_DOSSIER_USE_LLM", "false")

from agents.rnd_ceo_agent import RndCeoAgent  # noqa: E402
from agents.rnd_product_agent import RndProductAgent  # noqa: E402
from agents.rnd_social_agent import RndSocialAgent  # noqa: E402
from agents.rnd_visual_agent import RndVisualAgent  # noqa: E402
from services.rnd_pipeline import build_dossier_pipeline  # noqa: E402
from services.rnd_repository import get_rnd_repository  # noqa: E402

SECTION_KEYS = [
    ("problem", "Problème", "Douleur utilisateur concrète avec chiffres."),
    ("solution", "Solution", "Produit ALNUA qui automatise le workflow."),
    ("market", "Marché", "Concurrent Buffer — gap pricing solo créateurs."),
    ("mvp", "MVP", "- Import assets\n- Calendrier\n- Export 3 plateformes"),
    ("feasibility", "Faisabilité", "Next.js + Supabase + OpenRouter."),
    ("business_case", "Business case", "SaaS 16-49€/mois."),
    ("risks", "Risques", "APIs Meta instables."),
    ("decision", "Décision", "GO — valider pricing M6."),
]


def test_full_pipeline_e2e() -> None:
    repo = get_rnd_repository()
    ceo = RndCeoAgent()
    visual = RndVisualAgent()
    social = RndSocialAgent()
    product = RndProductAgent()

    legacy_id = f"test_e2e_{uuid.uuid4().hex[:8]}"
    idea_row = repo.db.insert(
        "rnd_ideas",
        {
            "legacy_id": legacy_id,
            "title": "E2E Pipeline Test",
            "description": "Phase 8 full pipeline",
            "domain": "saas",
            "source": "test",
            "status": "pending_evaluation",
        },
    )
    idea_row = idea_row[0] if isinstance(idea_row, list) else idea_row

    slug = f"test-e2e-{uuid.uuid4().hex[:6]}"
    dossier_row = repo.db.insert(
        "rnd_dossiers",
        {
            "idea_id": idea_row["id"],
            "slug": slug,
            "title": "E2E Pipeline Test",
            "tagline": "Test pipeline complet ALNUA",
            "domain": "saas",
            "branch": "app",
            "status": "ready_for_ceo",
            "ceo_status": "pending",
        },
    )
    dossier_row = dossier_row[0] if isinstance(dossier_row, list) else dossier_row
    dossier_id = str(dossier_row["id"])

    finance = {
        "capex_eur": 800,
        "verdict_finance": "viable",
        "revenue_hypothesis": {
            "pricing_model": {
                "model_type": "subscription",
                "tiers": [{"name": "Pro", "price_eur": 29.0}],
            },
        },
    }

    for sort_order, (key, title, content) in enumerate(SECTION_KEYS):
        repo.db.insert(
            "rnd_dossier_sections",
            {
                "dossier_id": dossier_id,
                "section_key": key,
                "title": title,
                "content_md": content,
                "sort_order": (sort_order + 1) * 10,
                "status": "validated",
            },
        )

    repo.db.update(
        "rnd_dossiers",
        dossier_id,
        {
            "finance_json": finance,
            "committee_report_md": "## Décisions\n- GO MVP\n\n**Verdict :** GO",
        },
    )

    page_id: str | None = None
    roadmap_ids: list[str] = []
    project_id: str | None = None

    try:
        # Phase 4 — visuals
        vis = visual.generate_assets(dossier_id, force=True)
        assert vis["created"] >= 1, "visuals failed"

        # Phase 6 — CEO approve + dispatch
        ceo.generate_package(dossier_id, force=True)
        ceo.record_ceo_decision(dossier_id, ceo_status="approved", ceo_note="E2E test")
        dispatch = ceo.dispatch_to_coo(dossier_id)
        roadmap_ids = [r["id"] for r in dispatch.get("roadmap_items", []) if r.get("id")]
        project_id = dispatch.get("project_id")

        # Phase 5 — social calendar (post-CEO)
        cal = social.generate_calendar(dossier_id, force=True)
        assert cal.get("created", 0) >= 1 or len(cal.get("calendar", [])) >= 1

        # Phase 7 — product publish
        prod = product.generate_product_page(dossier_id, force=True)
        page_id = prod["page"]["id"]
        pub = product.publish_product_page(dossier_id)
        assert pub["public_url"]

        public = product.get_public_page(slug)
        assert public["published"] is True

        dossier = repo.get_dossier(dossier_id)
        assert dossier is not None
        pipeline = build_dossier_pipeline(dossier)
        assert pipeline["progress_pct"] >= 85, (
            f"progress too low: {pipeline['progress_pct']}% "
            f"({pipeline['stages_done']}/{pipeline['stages_total']})"
        )
        assert pipeline["stages_done"] >= 6

        print(
            f"OK e2e pipeline — slug={slug} progress={pipeline['progress_pct']}% "
            f"({pipeline['stages_done']}/{pipeline['stages_total']})"
        )
    finally:
        if page_id:
            repo.db.delete("rnd_product_pages", page_id)
        for rid in roadmap_ids:
            try:
                repo.db.delete("roadmap", rid)
            except Exception:
                pass
        for sec in repo.db.select("rnd_dossier_sections", filters={"dossier_id": dossier_id}):
            repo.db.delete("rnd_dossier_sections", sec["id"])
        for asset in repo.db.select("rnd_dossier_assets", filters={"dossier_id": dossier_id}):
            repo.db.delete("rnd_dossier_assets", asset["id"])
        for cal_row in repo.db.select("rnd_social_calendar", filters={"dossier_id": dossier_id}):
            repo.db.delete("rnd_social_calendar", cal_row["id"])
        for ev in repo.db.select("rnd_dossier_events", filters={"dossier_id": dossier_id}):
            repo.db.delete("rnd_dossier_events", ev["id"])
        for log in repo.db.select("agent_logs", filters={"project_id": project_id}, limit=20) if project_id else []:
            repo.db.delete("agent_logs", log["id"])
        repo.db.delete("rnd_dossiers", dossier_id)
        repo.db.delete("rnd_ideas", idea_row["id"])
        if project_id:
            try:
                repo.db.delete("projects", project_id)
            except Exception:
                pass


if __name__ == "__main__":
    test_full_pipeline_e2e()
    print("\nPhase 8 E2E passed.")
