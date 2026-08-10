"""
services/deep_research.py — Pipeline de recherche approfondie multi-rounds ALNUA.

Inspiré de deep-research (u14app, ⭐4.6k) — chaque round génère des findings,
le suivant les affine, le dernier vérifie et produit un rapport cité.

Usage:
    from services.deep_research import run_deep_research, quick_research

    # Recherche complète (3 rounds)
    report = run_deep_research(
        query="Meilleures pratiques LLM routing 2024",
        context="ALNUA Hub utilise OpenRouter avec tier fast/standard/premium",
        rounds=3,
        agent_id="rnd_agent"
    )

    # Recherche rapide (1 round, pas de vérification)
    quick = quick_research("FastAPI performance tips", agent_id="dev_backend")
"""
from __future__ import annotations

import logging
from typing import Any

from services.deep_research_models import ResearchReport, ResearchRound
from services.deep_research_prompts import get_system

logger = logging.getLogger(__name__)


def _run_single_round(
    query: str,
    previous_context: str,
    round_num: int,
    agent_id: str,
    temperature: float = 0.4,
) -> ResearchRound:
    """Exécute un round de recherche et retourne les findings structurés."""
    try:
        from agents.base import LLMClient, parse_json_response
        llm = LLMClient()

        context_section = ""
        if previous_context:
            context_section = f"\n\nCONTEXTE DES ROUNDS PRÉCÉDENTS :\n{previous_context}"

        instruction_map = {
            1: "Explore le sujet en largeur. Identifie les angles principaux, les acteurs clés, les questions ouvertes.",
            2: "Approfondis les gaps identifiés au round précédent. Cherche des données plus précises et des sources.",
            3: "Vérifie les claims du round précédent. Identifie ce qui est établi vs hypothétique. Formule des recommandations.",
        }
        instruction = instruction_map.get(round_num, f"Continue l'approfondissement (round {round_num}).")

        prompt = f"""SUJET DE RECHERCHE : {query}{context_section}

INSTRUCTION ROUND {round_num} : {instruction}

Génère un objet JSON avec :
- findings (list[string]): 4-8 findings concrets sur le sujet (chacun 1-2 phrases avec source si connue)
- sources_mentioned (list[string]): sources citées dans les findings (URLs, publications, noms)
- confidence (string): "high" | "medium" | "low" — confiance globale dans les findings
- gaps_identified (list[string]): 2-4 questions restées sans réponse à investiguer
- sub_query (string): question plus précise à investiguer au prochain round"""

        raw = llm.complete(get_system(agent_id), prompt, agent_id=agent_id, temperature=temperature)
        data = parse_json_response(raw)

        return ResearchRound(
            round_num=round_num,
            query=data.get("sub_query", query),
            findings=data.get("findings", []),
            sources_mentioned=data.get("sources_mentioned", []),
            confidence=data.get("confidence", "medium"),
            gaps_identified=data.get("gaps_identified", []),
        )
    except Exception as e:
        logger.warning(f"Research round {round_num} failed: {e}")
        return ResearchRound(
            round_num=round_num,
            query=query,
            findings=[f"Round {round_num} failed: {e}"],
            sources_mentioned=[],
            confidence="low",
            gaps_identified=["Erreur de recherche — réessayer"],
        )


def _synthesize_all_rounds(
    query: str,
    rounds: list[ResearchRound],
    context: str,
    agent_id: str,
) -> dict[str, Any]:
    """Synthèse finale de tous les rounds en rapport structuré."""
    try:
        from agents.base import LLMClient, parse_json_response
        llm = LLMClient()

        all_findings = []
        all_sources: set[str] = set()
        all_gaps: list[str] = []

        for r in rounds:
            all_findings.extend(r.findings)
            all_sources.update(r.sources_mentioned)
            all_gaps.extend(r.gaps_identified)

        findings_text = "\n".join(f"- {f}" for f in all_findings)
        sources_text = "\n".join(f"- {s}" for s in all_sources)

        prompt = f"""SUJET : {query}
CONTEXTE : {context or 'Aucun contexte supplémentaire'}

TOUS LES FINDINGS ({len(all_findings)}) :
{findings_text}

SOURCES MENTIONNÉES :
{sources_text}

Produis un rapport JSON final avec :
- executive_summary (string): résumé exécutif 3 phrases max — le plus important
- key_findings (list[object]): 5 findings clés, chacun {{finding, confidence, source}}
  - confidence: "🟢 Vérifié" | "🟡 Probable" | "🔴 Hypothèse"
- verified_claims (list[string]): claims qu'on peut affirmer avec confiance
- unverified_claims (list[string]): claims qui demandent validation
- knowledge_gaps (list[string]): ce qu'on n'a pas pu trouver
- recommended_actions (list[string]): 3-5 actions concrètes à prendre (format: "[agent_id] → action")"""

        raw = llm.complete(
            get_system(agent_id), prompt,
            agent_id=agent_id, temperature=0.3
        )
        return parse_json_response(raw)
    except Exception as e:
        logger.warning(f"Synthesis failed: {e}")
        return {
            "executive_summary": "Synthèse indisponible.",
            "key_findings": [],
            "verified_claims": [],
            "unverified_claims": [],
            "knowledge_gaps": list(set(all_gaps))[:5],
            "recommended_actions": [],
        }


def run_deep_research(
    query: str,
    context: str = "",
    rounds: int = 3,
    agent_id: str = "brainstorm",
    temperature: float = 0.4,
) -> dict[str, Any]:
    """
    Pipeline complet de recherche approfondie.

    rounds: 1=quick, 2=standard, 3=deep (recommandé)
    agent_id: "brainstorm" | "rnd_agent" | "analyst_business"

    Endpoint: POST /services/deep-research/run
    """
    rounds = max(1, min(5, rounds))
    depth_map = {1: "quick", 2: "standard", 3: "deep", 4: "deep", 5: "deep"}

    research_rounds: list[ResearchRound] = []
    previous_context = context

    for i in range(1, rounds + 1):
        logger.info(f"Deep research — round {i}/{rounds}: {query[:60]}")
        round_result = _run_single_round(
            query=query,
            previous_context=previous_context,
            round_num=i,
            agent_id=agent_id,
            temperature=temperature,
        )
        research_rounds.append(round_result)

        previous_context = "\n".join([
            f"Round {r.round_num}: {'; '.join(r.findings[:3])}"
            for r in research_rounds
        ])

    synthesis = _synthesize_all_rounds(query, research_rounds, context, agent_id)

    report = ResearchReport(
        query=query,
        agent_id=agent_id,
        rounds_completed=rounds,
        executive_summary=synthesis.get("executive_summary", ""),
        key_findings=synthesis.get("key_findings", []),
        verified_claims=synthesis.get("verified_claims", []),
        unverified_claims=synthesis.get("unverified_claims", []),
        knowledge_gaps=synthesis.get("knowledge_gaps", []),
        recommended_actions=synthesis.get("recommended_actions", []),
        rounds_history=research_rounds,
        depth=depth_map.get(rounds, "deep"),
    )

    try:
        from services.competition import add_points
        add_points(agent_id, "document_produced", note=f"Deep research: {query[:50]}")
    except Exception:
        pass

    return report.to_dict()


def quick_research(
    query: str,
    context: str = "",
    agent_id: str = "brainstorm",
) -> dict[str, Any]:
    """
    Recherche rapide en 1 round — pour les vérifications rapides.

    Endpoint: POST /services/deep-research/quick
    """
    return run_deep_research(query=query, context=context, rounds=1, agent_id=agent_id)
