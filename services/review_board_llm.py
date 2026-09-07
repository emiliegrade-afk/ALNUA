"""Optional Review Board LLM debate — flag-gated (Vague 3 / Phase 32+).

Enabled only when REVIEW_BOARD_LLM=1|true|yes. Default path stays structural.
"""

from __future__ import annotations

import os
from typing import Any

from services.input_sanitizer import sanitize_user_input


def llm_debate_enabled() -> bool:
    return os.getenv("REVIEW_BOARD_LLM", "").strip().lower() in ("1", "true", "yes", "on")


def run_optional_debate(
    *,
    department: str,
    artifact: dict[str, Any],
    gate: dict[str, Any],
    reviewers: list[str] | None,
) -> dict[str, Any] | None:
    """Return debate payload or None if flag off / LLM failure (caller keeps structural)."""
    if not llm_debate_enabled():
        return None

    roles = reviewers or ["qa", "pm", "coo"]
    roles = [str(r)[:40] for r in roles[:5]]
    brand_seats = {"brand", "content_company"}
    if brand_seats.intersection(roles):
        try:
            from services.brand_design_system import artifact_text
            from services.brand_voice_debate import debate_brand_voice

            text = artifact_text(artifact)
            if not text.strip():
                text = str(artifact.get("title") or artifact.get("name") or "artifact")
            debate = debate_brand_voice(
                text,
                department=department,
                sector=str(artifact.get("sector") or ""),
                rounds=1,
            )
            if not debate.get("deliberated"):
                return None
            return {
                "deliberated": True,
                "mode": "brand_elise_anouk",
                "debate": debate.get("debate") or {},
                "rounds": debate.get("rounds") or [],
                "reviewers": roles,
                "structural_brand": debate.get("structural"),
            }
        except Exception:
            return None

    try:
        from agents.base import LLMClient, parse_json_response
        from config.agent_personas import persona_prompt_intro
    except Exception:
        return None

    title = sanitize_user_input(
        str(artifact.get("title") or artifact.get("name") or "artifact"),
        max_length=200,
    )
    dept = sanitize_user_input(department, max_length=40)
    score = gate.get("score")
    threshold = gate.get("threshold")

    system = (
        f"{persona_prompt_intro('coo', role='COO')}. Tu animes un mini Review Board. "
        "Réponds en JSON valide uniquement."
    )
    prompt = f"""Département : {dept}
Artifact : {title}
Score structurel : {score} / seuil {threshold}
Reviewers : {", ".join(roles)}
Checks : {str(gate.get("checks", []))[:800]}

Produit un débat court :
{{
  "verdict": "approve|revise",
  "consensus": "1-2 phrases",
  "dissent": ["désaccord éventuel"],
  "actions": ["prochaine étape"]
}}"""
    try:
        raw = LLMClient().complete(system, prompt, agent_id="coo", temperature=0.2)
        debate = parse_json_response(raw)
        if not isinstance(debate, dict):
            return None
        return {
            "deliberated": True,
            "mode": "llm_flag",
            "debate": debate,
            "reviewers": roles,
        }
    except Exception:
        return None
