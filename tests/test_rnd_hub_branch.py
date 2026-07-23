"""Tests branche hub — dossiers R&D infra interne ALNUA."""

from __future__ import annotations

from services.rnd_dispatch_playbooks import get_playbook
from services.rnd_repository import RndRepository
from services.rnd_schemas import DOMAIN_TO_BRANCH


def test_domain_hub_maps_to_branch() -> None:
    assert DOMAIN_TO_BRANCH["hub"] == "hub"
    assert DOMAIN_TO_BRANCH["plateforme"] == "hub"
    assert DOMAIN_TO_BRANCH["infra"] == "hub"


def test_branch_for_domain_hub() -> None:
    assert RndRepository.branch_for_domain("hub") == "hub"
    assert RndRepository.branch_for_domain("plateforme") == "hub"


def test_hub_section_keys_lighter() -> None:
    keys = RndRepository.section_keys_for_domain("hub")
    assert "social_strategy" not in keys
    assert "market" not in keys
    assert "problem" in keys
    assert "decision" in keys


def test_hub_playbooks_target_alnua_hub() -> None:
    spec = get_playbook("spec", branch="hub")
    assert spec is not None
    assert spec.pole == "hub"
    assert "ALNUA_HUB" in spec.template

    dev_app = get_playbook("dev_app", branch="hub")
    assert dev_app is not None
    assert "web/src" in dev_app.template

    product_spec = get_playbook("dev_app", branch="app")
    assert product_spec is not None
    assert product_spec.pole == "app"
    assert "create-next-app" in product_spec.template.lower()


def test_resolve_branch_hub() -> None:
    from services.rnd_ceo_package import DISPATCH_POLES, resolve_branch
    from services.rnd_schemas import RndDossierOut

    dossier = RndDossierOut(
        id="test-id",
        idea_id="idea-1",
        slug="workflow-engine",
        title="Workflow Engine",
        domain="hub",
        branch="hub",
        status="draft",
        sections=[],
    )
    assert resolve_branch(dossier) == "hub"
    assert "dev_backend" in {r["agent_id"] for r in DISPATCH_POLES["hub"]}
    assert "marketing_agent" not in {r["agent_id"] for r in DISPATCH_POLES["hub"]}
