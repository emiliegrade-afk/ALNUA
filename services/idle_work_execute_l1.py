"""Idle L1 executors — real drafts (no publish / no L3 side-effects)."""

from __future__ import annotations

import logging
from typing import Any

from services.input_sanitizer import sanitize_user_input

logger = logging.getLogger(__name__)


def execute_company_draft(item: dict[str, Any]) -> dict[str, Any]:
    """Anouk — brouillon annonce marque (fichier seul, pas de queue_post)."""
    from skills.skill_content_company import gen_corporate_announcement

    payload = item.get("payload") or {}
    theme = sanitize_user_input(str(payload.get("theme") or item.get("title") or "ALNUA"))
    milestone = sanitize_user_input(str(payload.get("milestone_type") or "milestone"))
    draft = gen_corporate_announcement(theme[:400], milestone[:80] or "milestone")
    return {
        "status": "draft",
        "kind": "company_draft",
        "agent_id": "content_company",
        "draft": draft,
        "note": "Brouillon idle L1 — non publié (pas de queue_post)",
    }


def execute_product_triage(item: dict[str, Any]) -> dict[str, Any]:
    """Sam (PM) — propositions de tickets idle-ok (JSON), sans créer d'issues."""
    from agents.base import parse_json_response
    from agents.pm_agent import PMAgent

    instruction = sanitize_user_input(
        "Triage idle ALNUA (sans créer d'issues GitHub). "
        "Propose 3 à 5 tickets candidats labellables idle-ok pour avancer "
        "Naïa / Wyrdheim / Eve / Hub. Réponds en JSON uniquement : "
        '{"tickets":[{"title":"...","branch":"app|gaming|robo|hub","priority":"P1|P2|P3","why":"..."}],'
        '"summary":"une phrase"}'
    )
    raw = PMAgent().handle_instruction(instruction)
    parsed = parse_json_response(raw) if isinstance(raw, str) else {}
    if not isinstance(parsed, dict):
        parsed = {"raw": str(raw)[:2000]}
    return {
        "status": "draft",
        "kind": "product_triage",
        "agent_id": "pm",
        "triage": parsed,
        "note": "Brouillon idle L1 — aucune issue créée",
    }


def execute_l1_item(item: dict[str, Any]) -> dict[str, Any]:
    kind = str(item.get("kind") or "")
    if kind == "company_draft":
        return execute_company_draft(item)
    if kind == "product_triage":
        return execute_product_triage(item)
    return {"status": "skipped", "kind": kind, "note": "not an L1 LLM kind"}
