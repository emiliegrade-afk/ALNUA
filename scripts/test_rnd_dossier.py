"""Tests for R&D Dossier phase 1 (repository, promote, API helpers)."""
from __future__ import annotations

import logging
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

import os

os.environ.setdefault("RND_DOSSIER_USE_LLM", "false")

from services.rnd_finance_estimate import estimate_rnd_project, finance_json_to_markdown  # noqa: E402
from services.rnd_deck_generator import build_deck_html, md_to_html, write_deck_files  # noqa: E402
from services.rnd_repository import get_rnd_repository  # noqa: E402
from services.rnd_schemas import SECTION_DEFINITIONS, RndDossierOut, RndDossierSectionOut  # noqa: E402
from agents.rnd_dossier_agent import RndDossierAgent  # noqa: E402


def test_schemas() -> None:
    assert "problem" in SECTION_DEFINITIONS
    assert "business_case" in SECTION_DEFINITIONS
    print("OK schemas")


def test_slug_and_branch() -> None:
    repo = get_rnd_repository()
    assert repo.branch_for_domain("app") == "app"
    assert repo.branch_for_domain("jeu") == "gaming"
    assert repo.branch_for_domain("hardware") == "robotics"
    keys = repo.section_keys_for_domain("jeu")
    assert "lore" in keys
    assert "manufacturing" not in keys
    hw_keys = repo.section_keys_for_domain("hardware")
    assert "manufacturing" in hw_keys
    print("OK branch + section keys")


def test_json_load() -> None:
    repo = get_rnd_repository()
    ideas = repo.get_top_ideas(limit=5)
    print(f"OK json/db load — {len(ideas)} ideas")
    if ideas:
        print(f"   sample: {ideas[0].title[:40]} | dossier={ideas[0].dossier_id}")


def test_finance_estimate() -> None:
    finance = estimate_rnd_project(
        title="CreatorFlow",
        description="Pipeline IA pour créateurs de contenu",
        domain="saas",
        effort="L",
        section_text="Pricing concurrent : 25-200$/mois selon taille audience",
    )
    assert finance["cost_model"] == "ai_solo"
    assert finance["capex_eur"] > 0
    assert finance["capex_eur"] < 2000, "AI solo CAPEX should stay modest"
    assert finance.get("capex_llm_agents_eur", 0) > 0
    assert finance["opex_incremental_eur"] is not None
    rev = finance["revenue_hypothesis"]
    assert rev.get("pricing_model"), "revenue must include product pricing tiers"
    assert rev.get("m3_monthly_run_rate_eur", 0) > 0
    assert rev.get("m12_monthly_run_rate_eur", 0) >= 0
    assert rev.get("cumulative_12m_eur", 0) >= 0
    assert "net_impact_12m_eur" in finance
    assert finance["verdict_finance"] in ("viable", "tight", "no_go")
    md = finance_json_to_markdown(finance)
    assert "agents IA" in md or "OpenRouter" in md
    assert "M6" in md and "M12" in md
    assert "vont adorer" not in md.lower()
    print(
        f"OK finance AI solo — capex={finance['capex_eur']} "
        f"M12={rev.get('m12_monthly_run_rate_eur')} verdict={finance['verdict_finance']}"
    )


def test_enrich_and_validate() -> None:
    repo = get_rnd_repository()
    if not repo._use_db:
        print("SKIP enrich — Supabase unavailable")
        return

    legacy_id = f"test_enrich_{uuid.uuid4().hex[:8]}"
    test_idea = {
        "id": legacy_id,
        "title": "Test Enrich Phase 2",
        "description": "App test phase 2 avec analyse marché",
        "domain": "app",
        "effort": "S",
        "source": "test_script",
        "status": "evaluated",
        "score": 20,
        "verdict": "MAYBE",
        "agent_reasoning": "Marché nomade en croissance, concurrent Park4Night faible sur le coliving.",
        "lifecycle_status": "raw",
    }
    json_ideas = repo._load_json_ideas()
    json_ideas.append(test_idea)
    repo._save_json_ideas(json_ideas)
    repo.sync_idea_to_db(test_idea)

    agent = RndDossierAgent(repo)
    try:
        dossier, _ = repo.promote_idea_to_dossier(legacy_id, actor="test_script")
        enriched = agent.enrich_dossier(dossier.id, actor="test_script")
        assert enriched.finance_json is not None
        assert enriched.finance_json.get("capex_eur", 0) > 0
        bc = next(s for s in enriched.sections if s.section_key == "business_case")
        assert "CAPEX" in bc.content_md or "Business case" in bc.content_md

        validated = agent.validate_section(dossier.id, "business_case", actor="emilie")
        assert validated.sections_validated_count >= 1
        assert validated.status in ("partial_validated", "ready_for_ceo", "draft")
        print("OK enrich + validate section")
    finally:
        db_row = repo.get_idea_db_row(legacy_id)
        if db_row and db_row.get("dossier_id"):
            did = db_row["dossier_id"]
            for ev in repo.db.select("rnd_dossier_events", filters={"dossier_id": did}):
                repo.db.delete("rnd_dossier_events", ev["id"])
            for sec in repo.db.select("rnd_dossier_sections", filters={"dossier_id": did}):
                repo.db.delete("rnd_dossier_sections", sec["id"])
            repo.db.delete("rnd_dossiers", did)
            repo.db.update("rnd_ideas", db_row["id"], {"dossier_id": None, "lifecycle_status": "raw"})
        json_ideas = [i for i in repo._load_json_ideas() if i.get("id") != legacy_id]
        repo._save_json_ideas(json_ideas)
        print("OK cleanup enrich test")


def test_promote_and_cleanup() -> None:
    repo = get_rnd_repository()
    if not repo._use_db:
        print("SKIP promote — Supabase rnd_* tables not available")
        return

    legacy_id = f"test_promote_{uuid.uuid4().hex[:8]}"
    test_idea = {
        "id": legacy_id,
        "title": "Test Promote Dossier ALNUA",
        "description": "Idée de test pour validation phase 1",
        "domain": "app",
        "effort": "S",
        "source": "test_script",
        "status": "evaluated",
        "score": 22,
        "verdict": "GO",
        "reasoning": "Test automatique phase 1",
        "lifecycle_status": "raw",
    }
    json_ideas = repo._load_json_ideas()
    json_ideas.append(test_idea)
    repo._save_json_ideas(json_ideas)
    repo.sync_idea_to_db(test_idea)

    try:
        dossier, idea = repo.promote_idea_to_dossier(legacy_id, actor="test_script")
        assert dossier.slug
        assert len(dossier.sections) >= 8
        assert idea.dossier_id == dossier.id
        assert idea.lifecycle_status == "dossier_draft"
        print(f"OK promote -> {dossier.slug} ({len(dossier.sections)} sections)")

        # Duplicate promote must fail
        try:
            repo.promote_idea_to_dossier(legacy_id)
            raise AssertionError("Expected ValueError on duplicate promote")
        except ValueError:
            print("OK duplicate promote rejected")

        events = repo.get_dossier_events(dossier.id)
        assert any(e.event_type == "dossier_created" for e in events)
        print(f"OK events ({len(events)} logged)")

    finally:
        # Cleanup test data
        db_row = repo.get_idea_db_row(legacy_id)
        if db_row and db_row.get("dossier_id"):
            dossier_id = db_row["dossier_id"]
            try:
                for ev in repo.db.select(
                    "rnd_dossier_events", filters={"dossier_id": dossier_id}
                ):
                    repo.db.delete("rnd_dossier_events", ev["id"])
            except Exception:
                pass
            try:
                sections = repo.db.select("rnd_dossier_sections", filters={"dossier_id": dossier_id})
                for sec in sections:
                    repo.db.delete("rnd_dossier_sections", sec["id"])
            except Exception:
                pass
            try:
                repo.db.delete("rnd_dossiers", dossier_id)
            except Exception:
                pass
            try:
                repo.db.update("rnd_ideas", db_row["id"], {"dossier_id": None, "lifecycle_status": "raw"})
            except Exception:
                pass
        json_ideas = [i for i in repo._load_json_ideas() if i.get("id") != legacy_id]
        repo._save_json_ideas(json_ideas)
        print("OK cleanup test data")


def test_deck_generator() -> None:
    html = md_to_html("## Titre\n\n**Bold** et liste:\n\n- item A\n- item B")
    assert "<h2>" in html and "<strong>Bold</strong>" in html
    assert "<li>item A</li>" in html

    dossier = RndDossierOut(
        id=str(uuid.uuid4()),
        idea_id=str(uuid.uuid4()),
        slug="test-deck",
        title="Test Deck",
        tagline="One liner",
        domain="saas",
        branch="app",
        sections=[
            RndDossierSectionOut(
                id=str(uuid.uuid4()),
                dossier_id="x",
                section_key="problem",
                title="Problème",
                content_md="Les créateurs perdent 5h/semaine sur la monétisation multi-plateforme.",
            ),
        ],
        finance_json=estimate_rnd_project(
            title="Test",
            description="SaaS créateurs",
            domain="saas",
            effort="M",
        ),
    )
    deck_html = build_deck_html(dossier)
    assert "Test Deck" in deck_html
    assert "Problème" in deck_html

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "rnd_dossiers"
        result = write_deck_files(dossier, root=root, export_pdf=False)
        assert Path(result["html_path"]).is_file()
    print("OK deck generator")


def main() -> int:
    try:
        test_schemas()
        test_slug_and_branch()
        test_json_load()
        test_finance_estimate()
        test_deck_generator()
        test_promote_and_cleanup()
        test_enrich_and_validate()
        print("\n=== All phase 1-4 tests passed ===")
        return 0
    except Exception as exc:
        logging.exception("Test failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
