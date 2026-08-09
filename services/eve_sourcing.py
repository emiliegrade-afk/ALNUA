"""Eve robotics sourcing — alternatives, assembly plans, role split.

Uses current BOM as grounding. Prices/links are *estimates* to verify
before purchase — never auto-order. Pi may be offline.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from agents.base import LLMClient, parse_json_response
from services.input_sanitizer import sanitize_user_input
from skills.skill_bom import get_bom_context

logger = logging.getLogger(__name__)

_SYSTEM = (
    "Tu es expert hardware robotique pour Eve (ALNUA) — Raspberry Pi, "
    "capteurs, moteurs, alimentation. Réponds en JSON valide uniquement. "
    "Les prix sont des estimations à vérifier ; jamais d'achat automatique. "
    "Si le BOM est vide, propose une base minimale honnête sans inventer "
    "que ces pièces sont déjà en stock."
)


def _bom_block(category: str | None = None) -> str:
    ctx = get_bom_context(category=category, limit=40)
    if not ctx.get("ok"):
        return f"BOM indisponible: {ctx.get('error', '?')}"
    items = ctx.get("items") or []
    if not items:
        return "BOM actuel: vide (aucune pièce enregistrée)."
    return "BOM actuel:\n" + json.dumps(items, ensure_ascii=False)[:3500]


def suggest_alternatives(
    need: str,
    *,
    category: str | None = None,
    max_options: int = 4,
) -> dict[str, Any]:
    """Pro / budget alternatives for a component need, grounded on BOM."""
    need_clean = sanitize_user_input(need, max_length=400)
    if len(need_clean) < 3:
        raise ValueError("need trop court")
    cat = sanitize_user_input(category or "", max_length=40) or None
    n = max(2, min(int(max_options), 6))
    prompt = f"""Besoin composant Eve : {need_clean}
Catégorie hint : {cat or "libre"}
{_bom_block(cat)}

Propose jusqu'à {n} options en JSON :
{{
  "need": "...",
  "options": [
    {{
      "name": "référence concrète",
      "tier": "pro|budget|diy",
      "approx_price_eur": 0,
      "supplier_hint": "Mouser|Farnell|AliExpress|PiHut|autre",
      "pi_compat": "Pi 4/5 notes",
      "pros": ["..."],
      "cons": ["..."],
      "why_cheaper_or_better": "vs l'option pro / vs BOM actuel"
    }}
  ],
  "recommendation": "1 phrase",
  "verify_before_buy": ["point à vérifier"],
  "disclaimer": "Estimations — vérifier stock/prix/compat avant commande"
}}"""
    raw = LLMClient().complete(_SYSTEM, prompt, agent_id="electronics", temperature=0.35)
    result = parse_json_response(raw)
    if not isinstance(result, dict):
        return {"ok": False, "error": "Réponse LLM non JSON", "raw": str(raw)[:500]}
    result["ok"] = True
    result["bom_grounded"] = True
    return result


def assembly_plan(*, goal: str = "") -> dict[str, Any]:
    """Step-by-step montage plan from current BOM (+ goal)."""
    goal_clean = sanitize_user_input(goal or "Assembler Eve selon le BOM actuel", max_length=500)
    prompt = f"""Objectif montage : {goal_clean}
{_bom_block()}

Produis un plan de montage actionnable en JSON :
{{
  "title": "Plan de montage Eve",
  "prerequisites": ["outils / sécurité"],
  "steps": [
    {{
      "order": 1,
      "title": "string",
      "parts": ["composants BOM ou génériques"],
      "actions": ["actions concrètes"],
      "checks": ["comment valider l'étape"],
      "risks": ["sécurité / ESD / alim"]
    }}
  ],
  "wiring_notes": "GPIO / I2C / alim séparée servos si pertinent",
  "next_software": "ce que Zara (embedded) doit flasher / tester ensuite",
  "missing_from_bom": ["pièces absentes du BOM pour ce goal"]
}}
Si BOM vide : plan générique Pi + alim + 1 capteur, et liste missing_from_bom clairement."""
    raw = LLMClient().complete(_SYSTEM, prompt, agent_id="mechanical", temperature=0.3)
    result = parse_json_response(raw)
    if not isinstance(result, dict):
        return {"ok": False, "error": "Réponse LLM non JSON", "raw": str(raw)[:500]}
    result["ok"] = True
    return result


def infra_roles_blueprint(*, focus: str = "full") -> dict[str, Any]:
    """Who builds physical Eve vs companion app (Naïa-like)."""
    focus_clean = sanitize_user_input(focus or "full", max_length=80)
    prompt = f"""Focus : {focus_clean}
{_bom_block()}

Explique la répartition ALNUA pour Eve en JSON :
{{
  "physical_stack": {{
    "owner_agents": ["hardware", "electronics", "mechanical", "firmware", "embedded_dev", "industrial_design"],
    "deliverables": ["BOM", "schéma", "plan montage", "firmware", "SSH Pi"],
    "tools": ["Hub BOM", "SSH (PI_HOST) — pas WinSCP pour les agents"]
  }},
  "companion_app_stack": {{
    "owner_agents": ["dev_app", "dev_backend", "content_app"],
    "like_naia": true,
    "deliverables": ["app mobile/web liée à Eve", "API embodied", "UX"],
    "note": "dev_app ne soude pas le robot — il construit l'app compagnon"
  }},
  "handoffs": [
    {{"from": "hardware", "to": "embedded_dev", "artifact": "BOM + GPIO map"}},
    {{"from": "mechanical", "to": "industrial_design", "artifact": "plan montage / carénage"}},
    {{"from": "firmware", "to": "dev_app", "artifact": "contrat API télémétrie"}}
  ],
  "pi_status_policy": "PI_HOST optionnel ; offline = specs + BOM seulement",
  "summary_for_emilie": "3-5 phrases actionnables"
}}"""
    raw = LLMClient().complete(_SYSTEM, prompt, agent_id="hardware", temperature=0.25)
    result = parse_json_response(raw)
    if not isinstance(result, dict):
        return {"ok": False, "error": "Réponse LLM non JSON", "raw": str(raw)[:500]}
    result["ok"] = True
    return result
