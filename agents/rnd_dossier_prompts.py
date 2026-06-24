"""Prompts for R&D dossier section drafting (phase 2)."""

from __future__ import annotations

from config.agent_operating_spec import get_system_prompt

SECTION_DRAFT_SYSTEM = get_system_prompt("rnd_dossier_section_draft")
REVISE_SECTION_SYSTEM = get_system_prompt("rnd_dossier_section_revise")


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
