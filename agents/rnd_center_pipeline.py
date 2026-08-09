"""R&D Center — idea generation, evaluation, prototype, report."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

from agents.rnd_center_llm import _llm
from agents.rnd_center_store import _load_ideas
from config.agent_operating_spec import get_system_prompt

logger = logging.getLogger("rnd_center")

# ---------------------------------------------------------------------------
# Diversité domaines (éviter pipeline 100% vanlife)
# ---------------------------------------------------------------------------

_VANLIFE_KEYWORDS = (
    "vanlife", "van life", "van ", "camping", "nomad", "nomade", "vanlifeuse",
    "park4night", "ioverlander", "campendium", "fourgon", "vanlifer", "spot ",
    "aire de camping", "van trip",
)


def count_recent_vanlife_ideas(ideas: list[dict], limit: int = 15) -> int:
    """Compte les idées récentes orientées vanlife/nomad dans le pipeline."""
    recent = sorted(
        ideas,
        key=lambda i: i.get("created_at") or i.get("evaluated_at") or "",
        reverse=True,
    )[:limit]
    n = 0
    for idea in recent:
        blob = " ".join(
            str(idea.get(k) or "")
            for k in ("title", "description", "domain")
        ).lower()
        if any(kw in blob for kw in _VANLIFE_KEYWORDS):
            n += 1
    return n


def build_rnd_diversity_block(existing_titles: list[str], ideas: list[dict]) -> str:
    """Consignes anti-biais vanlife pour la génération d'idées."""
    van_count = count_recent_vanlife_ideas(ideas)
    lines = [
        "QUOTAS OBLIGATOIRES pour les 6 idées :",
        "- MAX 1 idée vanlife / nomad / camping / van / spots (adjacent NUAWAY)",
        "- AU MOINS 1 : jeu OU gaming OU Wyrdheim",
        "- AU MOINS 1 : robotique OU hardware OU Eve",
        "- AU MOINS 1 : app SANS lien vanlife (santé, Naïa, productivité, créateurs…)",
        "- AU MOINS 1 : SaaS B2B ou outil pro",
        "- Varie les domaines : app|jeu|robotique|hardware|saas|ia|autre",
    ]
    if van_count >= 4:
        lines.insert(
            0,
            f"ALERTE : {van_count} idées récentes déjà orientées vanlife — "
            "AUCUNE nouvelle idée nomad/van ce cycle sauf opportunité exceptionnelle.",
        )
    elif van_count >= 2:
        lines.insert(
            0,
            f"Note : {van_count} idées récentes vanlife — privilégier les autres marchés.",
        )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ÉTAPE 2 — Générer des idées (sans bride)
# ---------------------------------------------------------------------------

def _generate_ideas(market_obs: str, user_feedback: str, vision: str, existing_titles: list[str]) -> list[dict]:
    """
    Génère 5-8 idées nouvelles.
    Aucune limite de domaine. Créativité maximale.
    """
    existing = "\n".join(f"- {t}" for t in existing_titles[-20:]) if existing_titles else "Aucune"
    diversity = build_rnd_diversity_block(existing_titles, _load_ideas())

    system = get_system_prompt("rnd_idea_generator")

    user = f"""VISION ALNUA :
{vision}

{diversity}

OBSERVATIONS MARCHÉ :
{market_obs[:2000] if market_obs else "Non disponible"}

FEEDBACK UTILISATEURS :
{user_feedback[:1000] if user_feedback else "Non disponible"}

IDÉES DÉJÀ EXISTANTES (ne pas répéter) :
{existing}

Génère 6 idées nouvelles, respecte les QUOTAS ci-dessus."""

    try:
        raw = _llm(system, user, max_tokens=3000)
        # Parse JSON
        import re
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            ideas_raw = json.loads(match.group())
            ideas = []
            for idea in ideas_raw:
                ideas.append({
                    "id": f"idea_{int(datetime.now().timestamp())}_{len(ideas)}",
                    "title": idea.get("title", "")[:100],
                    "domain": idea.get("domain", "autre"),
                    "description": idea.get("elevator_pitch", ""),
                    "why_now": idea.get("why_now", ""),
                    "effort": idea.get("effort", "M"),
                    "source": "rnd_agent",
                    "status": "pending_evaluation",
                    "score": None,
                    "created_at": datetime.now().isoformat(),
                })
            return ideas
    except Exception as exc:
        logger.warning("rnd_center: generate_ideas failed: %s", exc)
    return []


# ---------------------------------------------------------------------------
# ÉTAPE 3 — Évaluer et scorer
# ---------------------------------------------------------------------------

def _evaluate_idea(idea: dict, vision: str) -> dict:
    """Score une idée sur 3 axes : marché, faisabilité ALNUA, alignement vision."""
    system = get_system_prompt("rnd_idea_evaluator")

    user = f"""VISION ALNUA : {vision[:500]}

IDÉE À ÉVALUER :
Titre : {idea['title']}
Domaine : {idea.get('domain', '?')}
Description : {idea.get('description', '')}
Pourquoi maintenant : {idea.get('why_now', '')}
Effort estimé : {idea.get('effort', 'M')}

Évalue cette idée."""

    try:
        raw = _llm(system, user, max_tokens=1500)
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            evaluation = json.loads(match.group())
            idea.update({
                "score": evaluation.get("total", 0),
                "market_score": evaluation.get("market_score", 0),
                "feasibility_score": evaluation.get("feasibility_score", 0),
                "vision_score": evaluation.get("vision_score", 0),
                "verdict": evaluation.get("verdict", "MAYBE"),
                "reasoning": evaluation.get("reasoning", ""),
                "next_step": evaluation.get("next_step", ""),
                "status": "evaluated",
            })
    except Exception as exc:
        logger.warning("rnd_center: evaluate_idea failed for '%s': %s", idea['title'], exc)
        idea["status"] = "evaluation_failed"

    return idea


# ---------------------------------------------------------------------------
# ÉTAPE 4 — Prototyper les meilleures idées
# ---------------------------------------------------------------------------

def _prototype_idea(idea: dict) -> str:
    """
    Pour les idées GO avec effort S ou M :
    - Génère une mini-spec (1 page)
    - Crée un ticket GitHub si c'est une amélioration produit existant
    - Sauvegarde le concept doc dans data/rnd_concepts/
    """
    concepts_dir = Path(os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")) / "data" / "rnd_concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)

    system = get_system_prompt("rnd_mini_spec")

    user = f"""Rédige la mini-spec pour :

Titre : {idea['title']}
Domaine : {idea.get('domain', '?')}
Description : {idea.get('description', '')}
Pourquoi maintenant : {idea.get('why_now', '')}
Effort : {idea.get('effort', 'M')}
Score : {idea.get('score', 0)}/30

Sois concis, concret et actionnable."""

    try:
        spec = _llm(system, user, max_tokens=2000)
        slug = "".join(c if c.isalnum() else "_" for c in idea['title'].lower())[:40]
        date = datetime.now().strftime("%Y%m%d")
        spec_file = concepts_dir / f"{date}_{slug}.md"
        spec_file.write_text(
            f"# {idea['title']}\n\n"
            f"**Domaine :** {idea.get('domain', '?')} | **Score :** {idea.get('score', 0)}/30 | "
            f"**Effort :** {idea.get('effort', 'M')}\n\n"
            f"---\n\n{spec}",
            encoding="utf-8",
        )
        logger.info("rnd_center: spec créée → %s", spec_file.name)
        return str(spec_file)
    except Exception as exc:
        logger.warning("rnd_center: prototype_idea failed: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# ÉTAPE 5 — Rapport hebdomadaire
# ---------------------------------------------------------------------------

def _build_report(new_ideas: list[dict], prototyped: list[str], cycle_date: str) -> str:
    go_ideas = [i for i in new_ideas if i.get("verdict") == "GO"]
    maybe_ideas = [i for i in new_ideas if i.get("verdict") == "MAYBE"]
    no_ideas = [i for i in new_ideas if i.get("verdict") == "NO"]

    lines = [
        f"🧪 Rapport R&D ALNUA — {cycle_date}",
        f"{'='*40}",
        "",
        f"📊 {len(new_ideas)} idées analysées ce cycle",
        f"✅ GO : {len(go_ideas)} | 🤔 MAYBE : {len(maybe_ideas)} | ❌ NO : {len(no_ideas)}",
        "",
    ]

    if go_ideas:
        lines.append("🚀 IDÉES GO — À explorer en priorité :")
        for idea in go_ideas[:3]:
            lines.append(
                f"\n• [{idea.get('domain', '?').upper()}] {idea['title']} (score {idea.get('score', '?')}/30)"
            )
            lines.append(f"  {idea.get('description', '')[:120]}")
            lines.append(f"  → {idea.get('next_step', '')[:100]}")

    if prototyped:
        lines.append(f"\n📄 {len(prototyped)} spec(s) rédigée(s) → data/rnd_concepts/")

    lines.append("\n🔍 Analyse concurrentielle complète → data/rnd_competitive/")

    if maybe_ideas:
        lines.append("\n🤔 MAYBE — À reconsidérer plus tard :")
        for idea in maybe_ideas[:3]:
            lines.append(f"  • {idea['title']} — {idea.get('reasoning', '')[:80]}")

    lines.append("\n💡 Pour injecter une idée : dis au COO 'explore l'idée de...'")
    lines.append("🎯 Pour changer le focus : dis au COO 'change le fil conducteur R&D vers...'")

    return "\n".join(lines)


async def _send_telegram(message: str) -> None:
    try:
        from telegram import Bot
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            return
        bot = Bot(token=token)
        # Découpe si > 4096 chars (limite Telegram)
        text = message[:4096]
        await bot.send_message(chat_id=int(chat_id), text=text)
    except Exception as exc:
        logger.warning("rnd_center: telegram failed: %s", exc)

