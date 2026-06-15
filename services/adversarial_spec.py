"""
services/adversarial_spec.py — Spec adversariale multi-LLM pour ALNUA Hub.

Inspiré de adversarial-spec (github.com/zscole/adversarial-spec) :
Fait débattre deux LLMs (Spec + QA) sur une spec jusqu'à consensus.
Idéal pour Léon Marchand (Spec) et Alex Okafor (QA).

Usage :
    from services.adversarial_spec import debate_spec, quick_adversarial_check

    result = debate_spec(
        spec_text="L'agent doit...",
        context="Feature: système de scoring compétition",
        rounds=2,
    )
    # result["consensus_spec"] = version finale convergée
    # result["divergences"] = points où les deux LLMs ne s'accordaient pas
    # result["rounds_history"] = historique complet du débat
"""

from __future__ import annotations

import json
from typing import Any

from agents.base import LLMClient, parse_json_response
from config.agent_personas import persona_prompt_intro

# ---------------------------------------------------------------------------
# Personas des deux débatteurs
# ---------------------------------------------------------------------------

_SPEC_INTRO = persona_prompt_intro("spec", role="Spec Rédacteur")
_QA_INTRO = persona_prompt_intro("qa", role="QA Engineer")

_SPEC_WRITER_SYSTEM = _SPEC_INTRO + """ — expert en rédaction de spécifications techniques.
Tu viens de rédiger une spec et tu dois la défendre face aux critiques du QA.
Quand le QA soulève une objection valide, tu l'intègres et améliores la spec.
Quand l'objection est non-fondée, tu expliques pourquoi et maintiens ta position.

Format de réponse JSON :
{
  "accepted_critiques": ["critique acceptée et intégrée"],
  "rejected_critiques": [{"critique": "...", "reason": "pourquoi elle est rejetée"}],
  "updated_spec": "La spec mise à jour avec les critiques acceptées",
  "confidence": "low|medium|high"
}"""

_QA_CRITIC_SYSTEM = _QA_INTRO + """ — expert en détection des ambiguïtés et failles dans les specs.
Tu lis une spec et tu cherches :
- Les cas limites non couverts
- Les ambiguïtés qui pourraient mener à des bugs
- Les contradictions internes
- Les exigences non testables
- Les dépendances implicites non mentionnées

Format de réponse JSON :
{
  "critiques": [
    {
      "severity": "critical|major|minor",
      "section": "Quelle partie de la spec",
      "issue": "Description du problème",
      "suggestion": "Comment le corriger"
    }
  ],
  "verdict": "approve|revise|reject",
  "blocking_issues": ["Issues critiques qui bloquent l'approbation"]
}"""


def _call_spec_writer(llm: LLMClient, spec: str, critiques: list[dict]) -> dict[str, Any]:
    prompt = f"""Voici ta spec actuelle :

{spec}

Le QA a soulevé ces critiques :
{json.dumps(critiques, ensure_ascii=False, indent=2)}

Réponds en JSON selon ton format."""
    raw = llm.complete(
        _SPEC_WRITER_SYSTEM, prompt, agent_id="spec", temperature=0.3, method_name="debate_spec"
    )
    try:
        return parse_json_response(raw)
    except Exception:
        return {"updated_spec": spec, "accepted_critiques": [], "rejected_critiques": [], "confidence": "low"}


def _call_qa_critic(llm: LLMClient, spec: str, context: str) -> dict[str, Any]:
    prompt = f"""Contexte du projet :
{context}

Spec à analyser :
{spec}

Analyse cette spec en QA senior. Réponds en JSON selon ton format."""
    raw = llm.complete(_QA_CRITIC_SYSTEM, prompt, agent_id="qa", temperature=0.2, method_name="debate_spec")
    try:
        return parse_json_response(raw)
    except Exception:
        return {"critiques": [], "verdict": "approve", "blocking_issues": []}


def debate_spec(
    spec_text: str,
    context: str = "",
    rounds: int = 2,
    stop_on_approve: bool = True,
) -> dict[str, Any]:
    """
    Fait débattre Léon (Spec) et Alex (QA) sur la spec donnée.

    Args:
        spec_text:       La spec initiale à affiner
        context:         Contexte du projet (aide le QA à mieux critiquer)
        rounds:          Nombre de tours de débat (défaut: 2, max recommandé: 3)
        stop_on_approve: Arrêter dès que le QA approuve (évite les tours inutiles)

    Returns:
        {
            "consensus_spec": str,       — version finale convergée
            "rounds_completed": int,
            "final_verdict": str,        — "approve" | "revise" | "reject"
            "divergences": [...],        — points de désaccord restants
            "rounds_history": [...],     — historique complet
            "quality_gain": str,         — estimation de l'amélioration
        }
    """
    llm = LLMClient()
    current_spec = spec_text
    history = []
    divergences: list[dict] = []

    for round_num in range(1, rounds + 1):
        # QA critique la spec courante
        qa_result = _call_qa_critic(llm, current_spec, context)
        critiques = qa_result.get("critiques", [])
        verdict = qa_result.get("verdict", "revise")

        if stop_on_approve and verdict == "approve":
            history.append({
                "round": round_num,
                "qa_verdict": "approve",
                "critiques_count": 0,
                "spec_updated": False,
            })
            break

        # Si pas de critiques, pas besoin d'itérer
        if not critiques:
            history.append({
                "round": round_num,
                "qa_verdict": verdict,
                "critiques_count": 0,
                "spec_updated": False,
            })
            break

        # Spec writer répond aux critiques
        spec_result = _call_spec_writer(llm, current_spec, critiques)
        updated_spec = spec_result.get("updated_spec", current_spec)
        rejected = spec_result.get("rejected_critiques", [])

        # Les critiques rejetées sont des divergences
        for r in rejected:
            if isinstance(r, dict):
                divergences.append({
                    "round": round_num,
                    "critique": r.get("critique", str(r)),
                    "spec_position": r.get("reason", ""),
                })

        history.append({
            "round": round_num,
            "qa_verdict": verdict,
            "critiques_count": len(critiques),
            "critiques_accepted": len(spec_result.get("accepted_critiques", [])),
            "critiques_rejected": len(rejected),
            "blocking_issues": qa_result.get("blocking_issues", []),
            "spec_updated": updated_spec != current_spec,
        })

        current_spec = updated_spec

    final_qa = _call_qa_critic(llm, current_spec, context)
    final_verdict = final_qa.get("verdict", "revise")

    # Estimation qualitative du gain
    initial_len = len(spec_text)
    final_len = len(current_spec)
    total_accepted = sum(r.get("critiques_accepted", 0) for r in history)
    quality_gain = (
        "significant" if total_accepted >= 3
        else "moderate" if total_accepted >= 1
        else "minimal"
    )

    return {
        "consensus_spec": current_spec,
        "rounds_completed": len(history),
        "final_verdict": final_verdict,
        "divergences": divergences,
        "rounds_history": history,
        "quality_gain": quality_gain,
        "stats": {
            "initial_spec_chars": initial_len,
            "final_spec_chars": final_len,
            "total_critiques_accepted": total_accepted,
            "total_divergences": len(divergences),
            "blocking_issues_remaining": final_qa.get("blocking_issues", []),
        },
    }


def quick_adversarial_check(spec_text: str, context: str = "") -> dict[str, Any]:
    """
    Version légère : un seul round QA sans itération.
    Retourne les problèmes trouvés sans modifier la spec.
    Utile pour un pre-check rapide avant le débat complet.
    """
    llm = LLMClient()
    qa_result = _call_qa_critic(llm, spec_text, context)
    critical = [c for c in qa_result.get("critiques", []) if c.get("severity") == "critical"]
    return {
        "verdict": qa_result.get("verdict", "revise"),
        "total_critiques": len(qa_result.get("critiques", [])),
        "critical_count": len(critical),
        "blocking_issues": qa_result.get("blocking_issues", []),
        "critiques": qa_result.get("critiques", []),
        "recommendation": (
            "Proceed to full debate" if qa_result.get("verdict") == "revise"
            else "Spec approved — no debate needed" if qa_result.get("verdict") == "approve"
            else "Spec needs major rework before debate"
        ),
    }
