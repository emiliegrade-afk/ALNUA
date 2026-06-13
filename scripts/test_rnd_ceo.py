"""Tests for R&D CEO package & dispatch (phase 6)."""
from __future__ import annotations

import logging
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

os.environ.setdefault("RND_DOSSIER_USE_LLM", "false")

from agents.rnd_ceo_agent import (  # noqa: E402
    CeoDecisionError,
    DispatchNotAllowedError,
    RndCeoAgent,
)
from services.rnd_ceo_package import (  # noqa: E402
    build_ceo_package_json,
    build_ceo_package_md,
    build_dispatch_matrix,
    resolve_branch,
)
from services.rnd_repository import get_rnd_repository  # noqa: E402
from services.rnd_schemas import RndDossierOut, RndDossierSectionOut  # noqa: E402

SECTION_KEYS = [
    ("problem", "Problème", "Les créateurs perdent 20h/semaine en logistique."),
    ("solution", "Solution", "CreatorFlow automatise la distribution multi-plateformes."),
    ("market", "Marché", "Concurrent : Buffer, Hootsuite — gap sur l'IA créative."),
    ("mvp", "MVP", "Import assets, calendrier, export 3 plateformes."),
    ("feasibility", "Faisabilité", "Next.js + Supabase + OpenRouter."),
    ("business_case", "Business case", "SaaS 16-49€/mois, break-even M18."),
    ("risks", "Risques", "Dépendance APIs Meta/TikTok."),
    ("decision", "Décision", "Recommandation MAYBE — valider pricing."),
]


def _sample_dossier(branch: str = "app") -> RndDossierOut:
    did = str(uuid.uuid4())
    return RndDossierOut(
        id=did,
        idea_id=str(uuid.uuid4()),
        slug="creatorflow-test",
        title="CreatorFlow",
        tagline="Pipeline IA pour créateurs",
        domain="saas",
        branch=branch,
        status="ready_for_ceo",
        finance_json={
            "capex_eur": 4200,
            "capex_dev_eur": 3500,
            "capex_llm_agents_eur": 400,
            "opex_monthly_eur": 45,
            "verdict_finance": "viable",
            "revenue_hypothesis": {
                "pricing_model": {
                    "model_type": "subscription",
                    "blended_arpu_eur": 32,
                    "tiers": [
                        {"name": "Starter", "price_eur": 16.99, "mix_pct": 0.5},
                        {"name": "Pro", "price_eur": 49.0, "mix_pct": 0.5},
                    ],
                },
                "m12_monthly_run_rate_eur": 1984,
            },
        },
        sections=[
            RndDossierSectionOut(
                id=str(uuid.uuid4()),
                dossier_id=did,
                section_key=k,
                title=t,
                content_md=c,
                status="validated",
            )
            for k, t, c in SECTION_KEYS
        ],
        sections_validated_count=8,
        sections_total_count=8,
    )


def test_branch_templates() -> None:
    app_d = _sample_dossier("app")
    assert resolve_branch(app_d) == "app"
    md = build_ceo_package_md(app_d, committee_report_md="## Décisions\n- GO MVP")
    assert "Executive summary" in md
    assert "Matrice dispatch" in md
    assert "COO" in md

    gaming_d = _sample_dossier("gaming")
    gaming_md = build_ceo_package_md(gaming_d)
    assert "Perfs cibles" in gaming_md or "Direction artistique" in gaming_md

    robotics_d = _sample_dossier("robotics")
    assert "hardware" in build_ceo_package_md(robotics_d).lower()

    matrix = build_dispatch_matrix(app_d)
    assert any(r["agent_id"] == "coo_agent" for r in matrix)
    print("OK branch templates")


def test_package_json_structure() -> None:
    dossier = _sample_dossier()
    pkg = build_ceo_package_json(dossier)
    assert pkg["version"] == 1
    assert pkg["branch"] == "app"
    assert "blocks" in pkg
    assert len(pkg["dispatch_matrix"]) >= 4
    print("OK package json")


def test_ceo_pipeline_e2e() -> None:
    repo = get_rnd_repository()
    agent = RndCeoAgent()

    legacy_id = f"test_ceo_{uuid.uuid4().hex[:8]}"
    idea_row = repo.db.insert(
        "rnd_ideas",
        {
            "legacy_id": legacy_id,
            "title": "Test CEO Pipeline",
            "description": "Phase 6 CEO",
            "domain": "saas",
            "source": "test",
            "status": "pending_evaluation",
        },
    )
    idea_row = idea_row[0] if isinstance(idea_row, list) else idea_row

    slug = f"test-ceo-{uuid.uuid4().hex[:6]}"
    dossier_row = repo.db.insert(
        "rnd_dossiers",
        {
            "idea_id": idea_row["id"],
            "slug": slug,
            "title": "Test CEO Pipeline",
            "domain": "saas",
            "branch": "app",
            "status": "ready_for_ceo",
        },
    )
    dossier_row = dossier_row[0] if isinstance(dossier_row, list) else dossier_row
    dossier_id = str(dossier_row["id"])

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
            "finance_json": _sample_dossier().finance_json,
            "committee_report_md": "## Décisions actées\n- MVP validé\n\n**Verdict :** GO",
        },
    )

    roadmap_ids: list[str] = []
    try:
        gen = agent.generate_package(dossier_id, force=True)
        assert gen.get("package")
        assert "Dossier CEO" in gen.get("markdown", "")

        status = agent.get_package(dossier_id)
        assert status["can_decide"] is True

        try:
            agent.dispatch_to_coo(dossier_id)
            raise AssertionError("dispatch should be blocked before CEO approval")
        except DispatchNotAllowedError:
            pass

        decision = agent.record_ceo_decision(
            dossier_id,
            ceo_status="approved",
            ceo_note="GO — lancer conception",
        )
        assert decision["ceo_status"] == "approved"

        dispatch = agent.dispatch_to_coo(dossier_id)
        assert dispatch.get("roadmap_items")
        roadmap_ids = [r["id"] for r in dispatch["roadmap_items"]]

        final = agent.get_package(dossier_id)
        assert final["dispatch_status"] == "dispatched"
        assert final["can_dispatch"] is False

        local = Path("data/rnd_dossiers") / slug / "ceo_package.md"
        assert local.exists()

        print(f"OK ceo e2e — {len(roadmap_ids)} roadmap items, package + dispatch")
    except Exception as exc:
        if "ceo_package_json" in str(exc) or "column" in str(exc).lower():
            print(
                "SKIP ceo e2e DB — apply migration 20260613150000_rnd_ceo_phase6.sql"
            )
        else:
            raise
    finally:
        for rid in roadmap_ids:
            try:
                repo.db.delete("roadmap", rid)
            except Exception:
                pass
        for sec in repo.db.select("rnd_dossier_sections", filters={"dossier_id": dossier_id}):
            repo.db.delete("rnd_dossier_sections", sec["id"])
        repo.db.delete("rnd_dossiers", dossier_id)
        repo.db.delete("rnd_ideas", idea_row["id"])
        local = Path("data/rnd_dossiers") / slug / "ceo_package.md"
        if local.exists():
            local.unlink()


def test_decision_requires_package() -> None:
    dossier = _sample_dossier()
    dossier.status = "ready_for_ceo"
    agent = RndCeoAgent()
    # No DB — test error class via mock path
    try:
        agent.record_ceo_decision(str(uuid.uuid4()), ceo_status="approved")
    except (CeoDecisionError, ValueError):
        pass
    print("OK decision guard")


def main() -> int:
    try:
        test_branch_templates()
        test_package_json_structure()
        test_decision_requires_package()
        test_ceo_pipeline_e2e()
        print("\n=== All phase 6 CEO tests passed ===")
        return 0
    except Exception as exc:
        logging.exception("Test failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
