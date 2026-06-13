"""
services/content_pipeline.py — Pipeline contenu multi-plateforme ALNUA.

Inspiré de content-pipeline (github.com/OrangeViolin/content-pipeline) :
Un brief → outputs formatés pour plusieurs plateformes en parallèle.
Intègre Sofia Reyes (Content) et Camille Rousseau (Marketing).

Usage :
    from services.content_pipeline import run_pipeline, ContentBrief

    result = run_pipeline(
        brief=ContentBrief(
            topic="Lancement fonctionnalité scoring compétition",
            product="ALNUA Hub",
            target_audience="Développeurs solo / indie studios",
            tone="tech, enthousiaste, direct",
            key_messages=["20 agents IA", "compétition gamifiée", "open source"],
        ),
        platforms=["twitter", "linkedin", "blog", "discord"],
    )
    # result["outputs"] = {"twitter": "...", "linkedin": "...", ...}
    # result["campaign_brief"] = brief stratégique Camille
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from agents.base import LLMClient, parse_json_response

# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class ContentBrief:
    """Brief d'entrée pour le pipeline contenu."""
    topic: str
    product: str
    target_audience: str
    tone: str = "professionnel, direct"
    key_messages: list[str] = field(default_factory=list)
    call_to_action: str = ""
    context: str = ""


# ---------------------------------------------------------------------------
# Formats par plateforme
# ---------------------------------------------------------------------------

PLATFORM_SPECS: dict[str, dict] = {
    "twitter": {
        "label": "Twitter/X",
        "max_chars": 280,
        "format": "1 tweet percutant + 2-3 tweets de thread optionnels. Hashtags pertinents.",
        "tone_modifier": "percutant, sans jargon, hook fort dès le début",
    },
    "linkedin": {
        "label": "LinkedIn",
        "max_chars": 3000,
        "format": "Post LinkedIn professionnel. Hook + développement + CTA. 3-5 emojis max.",
        "tone_modifier": "professionnel mais humain, storytelling, insight actionnable",
    },
    "blog": {
        "label": "Article blog",
        "max_chars": 8000,
        "format": "Article complet : titre accrocheur + intro + 3-4 sections H2 + conclusion + CTA.",
        "tone_modifier": "approfondi, exemples concrets, valeur pratique pour le lecteur",
    },
    "discord": {
        "label": "Discord/Slack",
        "max_chars": 2000,
        "format": "Message communauté décontracté. Peut inclure des blocs de code ou bullet points.",
        "tone_modifier": "casual, communauté, encourageant l'interaction",
    },
    "product_hunt": {
        "label": "Product Hunt",
        "max_chars": 500,
        "format": "Tagline courte + description 260 chars + first comment. Format PH.",
        "tone_modifier": "maker-friendly, enthousiaste, bénéfices concrets",
    },
    "email": {
        "label": "Email newsletter",
        "max_chars": 4000,
        "format": "Email newsletter : sujet + preheader + corps structuré + CTA bouton.",
        "tone_modifier": "personnel, direct, valeur immédiate pour l'abonné",
    },
    "github": {
        "label": "GitHub Release Notes",
        "max_chars": 3000,
        "format": "Release notes : ## What's New, ## Bug Fixes, ## Breaking Changes (si applicable). Bullet points techniques.",
        "tone_modifier": "technique, précis, orienté développeur",
    },
}

_CONTENT_SYSTEM = """Tu es Sofia Reyes, Content Strategist d'ALNUA.
Tu crées du contenu adapté à chaque plateforme, toujours ancré dans la valeur réelle du produit.
Camille (Marketing) fournit la stratégie, toi tu exécutes le contenu.
Réponds UNIQUEMENT en JSON valide selon le format demandé. Aucun texte hors JSON."""

_MARKETING_SYSTEM = """Tu es Camille Rousseau, Marketing Manager d'ALNUA.
Tu analyses le brief et construis la stratégie de communication : angle d'attaque, messages clés, positionnement.
Sofia (Content) implémente le contenu, toi tu fixes le cadre stratégique.
Réponds UNIQUEMENT en JSON valide selon le format demandé. Aucun texte hors JSON."""


def _generate_campaign_brief(llm: LLMClient, brief: ContentBrief) -> dict[str, Any]:
    """Camille génère le brief stratégique de campagne."""
    prompt = f"""Génère le brief stratégique de campagne pour ce lancement.

Produit : {brief.product}
Sujet : {brief.topic}
Audience : {brief.target_audience}
Ton : {brief.tone}
Messages clés : {', '.join(brief.key_messages) or 'À définir'}
CTA : {brief.call_to_action or 'À définir'}
Contexte : {brief.context or 'Standard'}

Réponds en JSON :
{{
  "campaign_angle": "L'angle d'attaque principal de la campagne",
  "core_message": "Le message central en une phrase",
  "refined_key_messages": ["Message 1", "Message 2", "Message 3"],
  "tone_guide": "Guide de ton pour tous les contenus",
  "cta_recommendation": "CTA recommandé",
  "do_list": ["À faire dans le contenu"],
  "dont_list": ["À éviter dans le contenu"],
  "target_persona": "Description précise du persona ciblé"
}}"""
    raw = llm.complete(_MARKETING_SYSTEM, prompt, agent_id="marketing", temperature=0.4)
    try:
        return parse_json_response(raw)
    except Exception:
        return {
            "campaign_angle": brief.topic,
            "core_message": f"Découvrez {brief.product}",
            "refined_key_messages": brief.key_messages,
            "tone_guide": brief.tone,
            "cta_recommendation": brief.call_to_action,
            "do_list": [],
            "dont_list": [],
            "target_persona": brief.target_audience,
        }


def _generate_platform_content(
    llm: LLMClient,
    brief: ContentBrief,
    campaign: dict[str, Any],
    platform: str,
) -> dict[str, Any]:
    """Sofia génère le contenu pour une plateforme spécifique."""
    spec = PLATFORM_SPECS.get(platform)
    if not spec:
        return {"platform": platform, "error": f"Plateforme inconnue: {platform}"}

    prompt = f"""Génère le contenu {spec['label']} pour cette campagne.

BRIEF CAMPAGNE :
- Produit : {brief.product}
- Sujet : {brief.topic}
- Angle : {campaign.get('campaign_angle', brief.topic)}
- Message central : {campaign.get('core_message', '')}
- Messages clés : {', '.join(campaign.get('refined_key_messages', brief.key_messages))}
- Guide de ton : {campaign.get('tone_guide', brief.tone)} | Modifier pour {spec['label']} : {spec['tone_modifier']}
- CTA : {campaign.get('cta_recommendation', brief.call_to_action)}
- À faire : {', '.join(campaign.get('do_list', [])[:3])}
- À éviter : {', '.join(campaign.get('dont_list', [])[:3])}

FORMAT PLATEFORME :
- Max chars : {spec['max_chars']}
- Format : {spec['format']}

Réponds en JSON :
{{
  "platform": "{platform}",
  "label": "{spec['label']}",
  "content": "Le contenu principal prêt à publier",
  "char_count": 0,
  "variations": ["Variante A si applicable", "Variante B si applicable"],
  "best_posting_time": "Recommandation horaire de publication",
  "hashtags": ["hashtag1", "hashtag2"],
  "notes": "Notes pour la personne qui publie"
}}"""

    raw = llm.complete(_CONTENT_SYSTEM, prompt, agent_id="content", temperature=0.5)
    try:
        result = parse_json_response(raw)
        if "content" in result and not result.get("char_count"):
            result["char_count"] = len(result["content"])
        return result
    except Exception:
        return {"platform": platform, "label": spec["label"], "error": "Parsing JSON échoué", "raw": raw[:200]}


async def _async_generate_all(
    brief: ContentBrief,
    campaign: dict[str, Any],
    platforms: list[str],
) -> list[dict[str, Any]]:
    """Génère tous les contenus plateforme en parallèle."""
    llm = LLMClient()
    loop = asyncio.get_event_loop()

    tasks = [
        loop.run_in_executor(
            None,
            lambda p=platform: _generate_platform_content(llm, brief, campaign, p)
        )
        for platform in platforms
    ]
    return await asyncio.gather(*tasks)


def run_pipeline(
    brief: ContentBrief,
    platforms: list[str] | None = None,
) -> dict[str, Any]:
    """
    Pipeline complet : brief → contenus multi-plateformes.

    1. Camille génère le brief stratégique de campagne
    2. Sofia génère les contenus en parallèle pour chaque plateforme

    Args:
        brief:     ContentBrief avec topic, product, audience, tone, messages
        platforms: Plateformes cibles (défaut: twitter, linkedin, blog, discord)

    Returns:
        {
            "campaign_brief": dict,   — brief stratégique Camille
            "outputs": {platform: content_dict},
            "stats": {...},
        }
    """
    if platforms is None:
        platforms = ["twitter", "linkedin", "blog", "discord"]

    # Filtrer les plateformes inconnues
    valid = [p for p in platforms if p in PLATFORM_SPECS]
    unknown = [p for p in platforms if p not in PLATFORM_SPECS]

    llm = LLMClient()

    # Étape 1 : brief stratégique (Camille)
    campaign = _generate_campaign_brief(llm, brief)

    # Étape 2 : contenus parallèles (Sofia)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, _async_generate_all(brief, campaign, valid))
                platform_outputs = future.result()
        else:
            platform_outputs = loop.run_until_complete(_async_generate_all(brief, campaign, valid))
    except RuntimeError:
        platform_outputs = asyncio.run(_async_generate_all(brief, campaign, valid))

    outputs = {item.get("platform", f"unknown_{i}"): item for i, item in enumerate(platform_outputs)}

    return {
        "campaign_brief": campaign,
        "outputs": outputs,
        "stats": {
            "platforms_requested": platforms,
            "platforms_generated": valid,
            "platforms_unknown": unknown,
            "total_chars_produced": sum(
                item.get("char_count", 0) for item in outputs.values()
            ),
            "product": brief.product,
            "topic": brief.topic,
        },
    }


def available_platforms() -> list[dict[str, str]]:
    """Retourne la liste des plateformes supportées."""
    return [
        {"id": pid, "label": spec["label"], "max_chars": spec["max_chars"]}
        for pid, spec in PLATFORM_SPECS.items()
    ]
