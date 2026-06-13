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
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class ResearchRound:
    round_num: int
    query: str
    findings: list[str]
    sources_mentioned: list[str]
    confidence: str    # "high" | "medium" | "low"
    gaps_identified: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "round": self.round_num,
            "query": self.query,
            "findings": self.findings,
            "sources_mentioned": self.sources_mentioned,
            "confidence": self.confidence,
            "gaps_identified": self.gaps_identified,
        }


@dataclass
class ResearchReport:
    query: str
    agent_id: str
    rounds_completed: int
    executive_summary: str
    key_findings: list[dict[str, str]]   # [{finding, confidence, source}]
    verified_claims: list[str]
    unverified_claims: list[str]
    knowledge_gaps: list[str]
    recommended_actions: list[str]
    rounds_history: list[ResearchRound]
    depth: str   # "quick" | "standard" | "deep"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "agent_id": self.agent_id,
            "rounds_completed": self.rounds_completed,
            "depth": self.depth,
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "verified_claims": self.verified_claims,
            "unverified_claims": self.unverified_claims,
            "knowledge_gaps": self.knowledge_gaps,
            "recommended_actions": self.recommended_actions,
            "rounds_history": [r.to_dict() for r in self.rounds_history],
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# System prompts par agent
# ---------------------------------------------------------------------------

_RESEARCHER_SYSTEMS: dict[str, str] = {
    "brainstorm": """Tu es Idris Okonkwo, Brainstorm Lead d'ALNUA.
Tu explores des idées en profondeur, tu croises les disciplines, tu fais émerger des connexions non-évidentes.
Ton rôle : transformer une question en carte d'exploration structurée.
Réponds en JSON valide.""",

    "rnd_agent": """Tu es Alex Mercer, R&D Lead d'ALNUA.
Tu analyses les approches techniques avec rigueur. Tu distingues ce qui est prouvé de ce qui est expérimental.
Ton rôle : évaluer la faisabilité, identifier les risques, proposer des prototypes concrets.
Réponds en JSON valide.""",

    "analyst_business": """Tu es Layla Hassan, Business Analyst d'ALNUA.
Tu analyses les tendances marché avec des données. Tu identifies des opportunités business.
Ton rôle : transformer une recherche en insight actionnable pour la direction.
Réponds en JSON valide.""",

    "default": """Tu es un chercheur expert d'ALNUA.
Tu analyses des sujets avec rigueur et méthode. Tu distingues les faits des hypothèses.
Réponds en JSON valide.""",
}


def _get_system(agent_id: str) -> str:
    return _RESEARCHER_SYSTEMS.get(agent_id, _RESEARCHER_SYSTEMS["default"])


# ---------------------------------------------------------------------------
# Round runner
# ---------------------------------------------------------------------------

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

        raw = llm.complete(_get_system(agent_id), prompt, agent_id=agent_id, temperature=temperature)
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


# ---------------------------------------------------------------------------
# Synthesizer final
# ---------------------------------------------------------------------------

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
            _get_system(agent_id), prompt,
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


# ---------------------------------------------------------------------------
# API principale
# ---------------------------------------------------------------------------

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

        # Construire le contexte cumulé pour le prochain round
        previous_context = "\n".join([
            f"Round {r.round_num}: {'; '.join(r.findings[:3])}"
            for r in research_rounds
        ])

    # Synthèse finale
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

    # Compétition — points pour la recherche
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
