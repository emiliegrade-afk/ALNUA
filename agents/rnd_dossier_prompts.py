"""Prompts for R&D dossier section drafting (phase 2)."""

from __future__ import annotations

ANTI_FLUFF_RULES = """
RÈGLES ANTI-FLUFF (obligatoires) :
- INTERDIT : "marché énorme", "les X vont adorer", "nostalgie", slogans sans preuve
- INTERDIT : chiffres ARR/MAU sans hypothèse de conversion explicite
- OBLIGATOIRE : nommer au moins 1 concurrent avec faiblesse documentée
- OBLIGATOIRE : lister ce que le MVP NE fait PAS (exclusions explicites)
- OBLIGATOIRE : hypothèses de pricing ou modèle économique
- Ton : analyste produit exigeant, pas copywriter marketing
"""

SECTION_DRAFT_SYSTEM = f"""Tu es l'analyste produit du département R&D d'ALNUA (solopreneuse nomade, agents IA).
Tu rédiges des sections de dossier R&D en markdown, concrètes et actionnables.

{ANTI_FLUFF_RULES}

Réponds UNIQUEMENT en JSON valide :
{{
  "sections": {{
    "problem": "markdown",
    "solution": "markdown",
    "market": "markdown",
    "mvp": "markdown",
    "feasibility": "markdown",
    "risks": "markdown",
    "decision": "markdown"
  }}
}}

Inclus uniquement les clés demandées. Chaque section : 150-400 mots, titres ## autorisés."""

REVISE_SECTION_SYSTEM = f"""Tu révises UNE section de dossier R&D ALNUA selon la note de révision d'Emilie.

{ANTI_FLUFF_RULES}

Réponds UNIQUEMENT en JSON : {{ "content_md": "markdown révisé" }}"""


def build_section_draft_user_prompt(
    *,
    title: str,
    description: str,
    domain: str,
    effort: str,
    why_now: str,
    reasoning: str,
    vision: str,
    competitive_context: str,
    section_keys: list[str],
) -> str:
    keys_str = ", ".join(section_keys)
    return f"""DOSSIER : {title}
Domaine : {domain} | Effort : {effort}

DESCRIPTION :
{description[:2000]}

POURQUOI MAINTENANT :
{why_now[:800] or 'Non précisé'}

ANALYSE AGENT R&D :
{reasoning[:1200] or 'Non précisé'}

VISION ALNUA :
{vision[:800]}

CONTEXTE CONCURRENTIEL (anti-patterns à éviter) :
{competitive_context[:1500] or 'Aucune analyse concurrentielle disponible.'}

Rédige les sections JSON : {keys_str}
Pour "mvp" : liste 5-8 features max + section "Hors scope MVP".
Pour "market" : TAM/SAM ordre de grandeur + 2 concurrents nommés + section "## Grille tarifaire proposée" avec tableau | Plan | Prix/mois EUR | Cible | (min 3 paliers, ex. 16,99 / 49 / 99 / 199).
Pour "feasibility" : stack ALNUA réaliste, dépendances, risques techniques.
Pour "decision" : recommandation honnête GO/MAYBE/NO avec justification."""
