"""Tests for R&D public product pages (phase 7)."""
from __future__ import annotations

import logging
import os
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

os.environ.setdefault("RND_DOSSIER_USE_LLM", "false")

from agents.rnd_product_agent import RndProductAgent  # noqa: E402
from services.rnd_product import (  # noqa: E402
    ProductPipelineLockedError,
    build_description_html,
    build_features,
    build_faq,
    build_product_page_payload,
    is_product_pipeline_unlocked,
)
from services.rnd_repository import get_rnd_repository  # noqa: E402
from services.rnd_schemas import RndDossierOut, RndDossierSectionOut  # noqa: E402

SECTION_KEYS = [
    ("problem", "Problème", "Les créateurs perdent 20h/semaine en logistique."),
    ("solution", "Solution", "CreatorFlow automatise la distribution multi-plateformes."),
    ("mvp", "MVP", "- Import assets\n- Calendrier éditorial\n- Export 3 plateformes"),
    ("risks", "Risques", "Dépendance APIs Meta/TikTok."),
    ("decision", "Décision", "Recommandation GO — valider pricing M6."),
]


def _sample_dossier(*, status: str = "ceo_approved", ceo_status: str = "approved") -> RndDossierOut:
    did = str(uuid.uuid4())
    return RndDossierOut(
        id=did,
        idea_id=str(uuid.uuid4()),
        slug=f"test-product-{uuid.uuid4().hex[:8]}",
        title="CreatorFlow",
        tagline="Pipeline IA pour créateurs",
        domain="saas",
        branch="app",
        status=status,  # type: ignore[arg-type]
        ceo_status=ceo_status,  # type: ignore[arg-type]
        finance_json={
            "revenue_hypothesis": {
                "pricing_model": {
                    "model_type": "subscription",
                    "tiers": [{"name": "Pro", "price_eur": 29.0}],
                },
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
        sections_validated_count=len(SECTION_KEYS),
        sections_total_count=len(SECTION_KEYS),
    )


def test_unlock_rules() -> None:
    assert is_product_pipeline_unlocked("draft", "pending") is False
    assert is_product_pipeline_unlocked("ready_for_ceo", "pending") is False
    assert is_product_pipeline_unlocked("ceo_approved", "approved") is True
    assert is_product_pipeline_unlocked("in_conception", "approved") is True
    assert is_product_pipeline_unlocked("partial_validated", "approved") is True
    print("OK product unlock rules")


def test_builders() -> None:
    dossier = _sample_dossier()
    html = build_description_html(dossier)
    assert "problème" in html.lower() or "solution" in html.lower()
    features = build_features(dossier)
    assert len(features) >= 2
    faq = build_faq(dossier)
    assert len(faq) >= 2
    payload = build_product_page_payload(dossier, project_id=None, hero_asset_id=None)
    assert payload["slug"] == dossier.slug
    assert payload["waitlist_enabled"] is True
    print(f"OK builders — {len(features)} features, {len(faq)} faq items")


def test_product_e2e_db() -> None:
    repo = get_rnd_repository()
    agent = RndProductAgent()

    legacy_id = f"test_product_{uuid.uuid4().hex[:8]}"
    idea_row = repo.db.insert(
        "rnd_ideas",
        {
            "legacy_id": legacy_id,
            "title": "Test Product Page",
            "description": "Phase 7 fiche produit",
            "domain": "saas",
            "source": "test",
            "status": "pending_evaluation",
        },
    )
    idea_row = idea_row[0] if isinstance(idea_row, list) else idea_row

    slug = f"test-product-{uuid.uuid4().hex[:6]}"
    dossier_row = repo.db.insert(
        "rnd_dossiers",
        {
            "idea_id": idea_row["id"],
            "slug": slug,
            "title": "Test Product Page",
            "tagline": "Landing ALNUA test",
            "domain": "saas",
            "branch": "app",
            "status": "ceo_approved",
            "ceo_status": "approved",
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
        {"finance_json": _sample_dossier().finance_json},
    )

    page_id: str | None = None
    try:
        status = agent.product_status(dossier_id)
        assert status["unlocked"] is True

        gen = agent.generate_product_page(dossier_id, force=True)
        assert gen["page"]["slug"] == slug
        assert gen["page"]["features"]
        page_id = gen["page"]["id"]

        pub = agent.publish_product_page(dossier_id)
        assert pub["public_url"]
        assert "/p/" in pub["public_url"]

        public = agent.get_public_page(slug)
        assert public["published"] is True
        assert public["title"] == "Test Product Page"

        agent.unpublish_product_page(dossier_id)
        try:
            agent.get_public_page(slug)
            raise AssertionError("expected ValueError for unpublished page")
        except ValueError:
            pass

        print(f"OK product e2e — slug={slug}")
    finally:
        if page_id:
            repo.db.delete("rnd_product_pages", page_id)
        for sec in repo.db.select("rnd_dossier_sections", filters={"dossier_id": dossier_id}):
            repo.db.delete("rnd_dossier_sections", sec["id"])
        for ev in repo.db.select("rnd_dossier_events", filters={"dossier_id": dossier_id}):
            repo.db.delete("rnd_dossier_events", ev["id"])
        repo.db.delete("rnd_dossiers", dossier_id)
        repo.db.delete("rnd_ideas", idea_row["id"])


def test_locked_dossier_raises() -> None:
    repo = get_rnd_repository()
    dossiers = repo.list_dossiers(limit=10)
    locked = next(
        (d for d in dossiers if d.ceo_status != "approved" and d.status not in ("ceo_approved", "in_conception", "published")),
        None,
    )
    if not locked:
        print("SKIP locked test — no draft dossier")
        return
    agent = RndProductAgent()
    try:
        agent.generate_product_page(locked.id)
        raise AssertionError("expected ProductPipelineLockedError")
    except ProductPipelineLockedError:
        print(f"OK locked guard — dossier={locked.slug}")


if __name__ == "__main__":
    test_unlock_rules()
    test_builders()
    test_locked_dossier_raises()
    test_product_e2e_db()
    print("\nAll phase 7 product tests passed.")
