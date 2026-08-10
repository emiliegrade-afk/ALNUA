"""LLM ideation, evaluation, and investigation for hypothesis trees."""

from __future__ import annotations

import logging
from typing import Any

from services.rnd_hypothesis_tree_helpers import (
    NodeStatus,
    _ancestor_insights,
    _match_watch_topics,
)

logger = logging.getLogger(__name__)


def _ideate_branches(
    topic: str, parent: dict[str, Any], tree: dict[str, Any], *, max_count: int = 3
) -> list[dict[str, str]]:
    """Propose child hypotheses conditioned on topic + ancestor insights."""
    from agents.base import LLMClient, parse_json_response

    ancestors = _ancestor_insights(tree, parent["id"])
    watch = _match_watch_topics(topic)
    watch_block = ""
    if watch:
        parts = []
        for w in watch:
            parts.append(f"**{w.get('title')}** — {w.get('summary', '')[:300]}")
            for branch in w.get("suggested_branches") or []:
                parts.append(f"  → branche suggérée : {branch}")
        watch_block = "\n\nVeille R&D ALNUA (prioriser si pertinent) :\n" + "\n".join(parts)

    system = """Tu es Alex Mercer, lead R&D ALNUA (solopreneuse CEO Emilie).
Propose des hypothèses ENFANTS testables pour un arbre de recherche (style Arbor).
Chaque branche = une direction produit/marché distincte, pas un doublon.

JSON uniquement :
{
  "branches": [
    {"title": "Nom court", "hypothesis": "Ce qu'on teste et pourquoi ALNUA"}
  ]
}

Règles :
- 2 à 3 branches max
- Diversité : gaming, robotique, SaaS, hardware, IA tooling — pas que vanlife
- Si une veille est fournie (ex. DiffusionGemma), au moins une branche peut l'exploiter
- Évite les hypothèses déjà explorées/prunées listées"""

    pruned = [
        f"- {n['title']}: {n.get('insight', '')[:120]}"
        for n in (tree.get("nodes") or {}).values()
        if n.get("status") == "pruned"
    ]
    pruned_block = "\n".join(pruned[:6]) if pruned else "aucune"

    user = f"""Sujet racine : {topic}
Parent : {parent['title']}
Hypothèse parent : {parent.get('hypothesis', '')[:400]}

Insights ancêtres :
{ancestors or 'aucun'}

Branches déjà écartées :
{pruned_block}
{watch_block}

Propose {max_count} branches enfants."""

    try:
        llm = LLMClient()
        raw = llm.complete(system, user, agent_id="rnd_agent", temperature=0.7)
        parsed = parse_json_response(raw)
        branches = parsed.get("branches") or []
        out: list[dict[str, str]] = []
        for b in branches[:max_count]:
            if isinstance(b, dict) and b.get("title"):
                out.append(
                    {
                        "title": str(b["title"])[:200],
                        "hypothesis": str(b.get("hypothesis") or b["title"])[:2000],
                    }
                )
        if out:
            return out
    except Exception as exc:
        logger.warning("hypothesis ideation LLM failed: %s", exc)

    return [
        {
            "title": f"{topic} — marché B2B",
            "hypothesis": f"Opportunité B2B autour de {topic} pour PME tech",
        },
        {
            "title": f"{topic} — intégration Hub ALNUA",
            "hypothesis": f"Comment {topic} améliore les agents ou réduit les coûts Hub",
        },
        {
            "title": f"{topic} — produit consommateur",
            "hypothesis": f"Version grand public / indie viable pour {topic}",
        },
    ][:max_count]


def _evaluate_node(hypothesis: str, report: dict[str, Any], vision: str) -> dict[str, Any]:
    from agents.base import LLMClient, parse_json_response

    summary = report.get("executive_summary") or ""
    findings = report.get("key_findings") or []
    findings_text = "\n".join(f"- {f}" for f in findings[:6])

    system = """Tu évalues une hypothèse R&D après investigation.
JSON uniquement :
{
  "market_score": 7,
  "feasibility_score": 6,
  "vision_score": 7,
  "total": 20,
  "verdict": "GO|MAYBE|NO",
  "insight": "Leçon courte à transmettre aux branches sœurs (1-2 phrases)",
  "decision": "merged|explored|pruned"
}

decision :
- merged si total >= 22 et opportunité claire pour ALNUA
- pruned si total < 14 ou marché/hypothèse invalidée
- explored sinon"""

    user = f"""VISION : {vision[:400]}
HYPOTHÈSE : {hypothesis[:500]}
RÉSUMÉ : {summary[:800]}
FINDINGS :
{findings_text[:1200]}"""

    try:
        llm = LLMClient()
        raw = llm.complete(system, user, agent_id="rnd_agent", temperature=0.3)
        parsed = parse_json_response(raw)
        decision = str(parsed.get("decision", "explored")).lower()
        if decision not in ("merged", "explored", "pruned"):
            total = int(parsed.get("total") or 0)
            decision = "merged" if total >= 22 else "pruned" if total < 14 else "explored"
        status: NodeStatus = decision  # type: ignore[assignment]
        return {
            "score": parsed.get("total"),
            "verdict": parsed.get("verdict"),
            "insight": str(parsed.get("insight") or "")[:500],
            "status": status,
            "scores_detail": {
                "market": parsed.get("market_score"),
                "feasibility": parsed.get("feasibility_score"),
                "vision": parsed.get("vision_score"),
            },
        }
    except Exception as exc:
        logger.warning("node evaluation failed: %s", exc)
        return {
            "score": None,
            "verdict": "MAYBE",
            "insight": summary[:300] if summary else "Investigation terminée — évaluation manuelle recommandée.",
            "status": "explored",
            "scores_detail": {},
        }


def _run_investigation(query: str) -> dict[str, Any]:
    from services.deep_research import quick_research
    from skills.skill_web_research import _search

    web_hits = _search(query, max_results=5)
    context_parts = [
        f"- {hit.get('title', '')}: {(hit.get('content') or '')[:250]}"
        for hit in web_hits
        if hit.get("title") or hit.get("content")
    ]
    context = "Résultats web récents:\n" + "\n".join(context_parts) if context_parts else ""
    return quick_research(query=query, context=context, agent_id="rnd_agent")


def _format_node_report(topic: str, node: dict[str, Any], report: dict[str, Any]) -> str:
    from services.coo_telegram_intents import _format_investigation_report

    header = f"🌳 **Arbre R&D** — branche « {node['title']} »\nSujet : {topic[:80]}\n\n"
    return header + _format_investigation_report(node["hypothesis"], report)[:3500]
