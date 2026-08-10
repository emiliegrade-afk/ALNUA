"""Idle L1 executors — drafts without publish. Offline-safe when no OpenRouter."""

from __future__ import annotations

import logging
from typing import Any

from services.input_sanitizer import sanitize_user_input

logger = logging.getLogger(__name__)


def _offline_mode() -> bool:
    try:
        from config.settings import settings

        if getattr(settings, "idle_offline_mode", False):
            return True
    except Exception:
        pass
    # No key / empty → treat as offline for idle L1
    try:
        from config.settings import settings

        key = str(getattr(settings, "openrouter_api_key", "") or "").strip()
        return not key
    except Exception:
        return False


def execute_company_draft(item: dict[str, Any]) -> dict[str, Any]:
    """Anouk — brouillon annonce marque (templates, pas de queue_post)."""
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
        "offline": True,
        "note": "Brouillon idle L1 — non publié (pas de queue_post)",
    }


def _offline_product_triage() -> dict[str, Any]:
    from services.idle_work_deliverables import offline_triage_tickets

    return {
        "tickets": offline_triage_tickets(),
        "summary": "Triage offline (sans OpenRouter) — candidats idle-ok",
        "offline": True,
    }


def execute_product_triage(item: dict[str, Any]) -> dict[str, Any]:
    """Sam (PM) — propositions tickets idle-ok. Fallback template si offline/LLM down."""
    if _offline_mode():
        return {
            "status": "draft",
            "kind": "product_triage",
            "agent_id": "pm",
            "triage": _offline_product_triage(),
            "note": "Brouillon idle L1 offline — aucune issue créée",
        }

    try:
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
        if not isinstance(parsed, dict) or not parsed.get("tickets"):
            parsed = _offline_product_triage()
            parsed["fallback"] = "empty_or_invalid_llm"
    except Exception as exc:
        logger.warning("product_triage LLM failed, offline fallback: %s", exc)
        parsed = _offline_product_triage()
        parsed["fallback"] = str(exc)[:200]

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
