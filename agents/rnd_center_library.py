"""R&D Center — library / CEO report → ideas development."""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Any

from agents.rnd_center_llm import _llm
from agents.rnd_center_pipeline import _evaluate_idea, _prototype_idea
from agents.rnd_center_store import _load_ideas, _save_ideas, get_vision
from config.agent_operating_spec import get_system_prompt

logger = logging.getLogger("rnd_center")

def _expand_library_concept(
    title: str,
    summary: str,
    *,
    topics: list[str] | None = None,
    source_url: str = "",
    query: str = "",
    bureau: str = "rd",
    vision: str = "",
) -> dict:
    """Enrichit une fiche bibliothèque en concept R&D structuré (comme le cycle autonome)."""
    topics_text = ", ".join(topics or []) or "non précisé"
    system = get_system_prompt("rnd_library_expand")

    user = f"""VISION ALNUA :
{vision[:800] or "CEO solopreneure — portfolio apps, gaming, robotique, agents IA autonomes."}

FICHE BIBLIOTHÈQUE :
- Bureau : {bureau}
- Titre : {title}
- Résumé : {summary[:2500]}
- Sujets : {topics_text}
- Recherche d'origine : {query[:300]}
- Source : {source_url[:500]}

Développe ce concept en proposition R&D actionnable (pas une simple reprise du résumé)."""

    base = {
        "title": title[:200],
        "domain": "autre",
        "description": summary[:4000] or title,
        "why_now": "",
        "effort": "M",
    }
    try:
        raw = _llm(system, user, max_tokens=2000)
        import re

        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            parsed = json.loads(match.group())
            if isinstance(parsed, dict):
                base.update(
                    {
                        "title": str(parsed.get("title") or title)[:200],
                        "domain": str(parsed.get("domain") or "autre"),
                        "description": str(parsed.get("description") or summary)[:4000],
                        "why_now": str(parsed.get("why_now") or "")[:2000],
                        "effort": str(parsed.get("effort") or "M")[:4],
                    }
                )
                insights = str(parsed.get("library_insights") or "").strip()
                if insights:
                    base["description"] = f"{base['description']}\n\n**Apport bibliothèque :** {insights}"
    except Exception as exc:
        logger.warning("rnd_center: expand_library_concept failed: %s", exc)

    return base


def develop_idea_from_library(
    *,
    title: str,
    summary: str = "",
    topics: list[str] | None = None,
    source_url: str = "",
    query: str = "",
    bureau: str = "rd",
    library_entry_id: str | None = None,
    source: str = "bibliothèque",
    prototype_if_go: bool = True,
    existing_id: str | None = None,
) -> dict:
    """
    Transforme une fiche bibliothèque en proposition R&D complète :
    enrichissement → scoring → mini-spec si GO (même pipeline que le cycle R&D).
    """
    ideas = _load_ideas()
    if library_entry_id:
        for existing in ideas:
            if existing.get("library_entry_id") == library_entry_id and existing.get("score") is not None:
                return existing

    vision = get_vision()
    expanded = _expand_library_concept(
        title,
        summary or title,
        topics=topics,
        source_url=source_url,
        query=query,
        bureau=bureau,
        vision=vision,
    )

    idea: dict[str, Any] = {
        "id": existing_id or f"idea_{int(datetime.now().timestamp())}",
        "title": expanded["title"],
        "domain": expanded.get("domain", "autre"),
        "description": expanded.get("description", summary),
        "why_now": expanded.get("why_now", ""),
        "effort": expanded.get("effort", "M"),
        "source": source,
        "status": "pending_evaluation",
        "score": None,
        "created_at": datetime.now().isoformat(),
        "lifecycle_status": "raw",
        "library_entry_id": library_entry_id,
        "library_query": query[:500] if query else None,
    }

    idea_id = idea["id"]
    library_meta = {
        k: idea[k]
        for k in ("library_entry_id", "library_query", "source", "lifecycle_status", "created_at")
        if k in idea
    }
    idea = _evaluate_idea(idea, vision)
    idea.update(library_meta)
    idea["id"] = idea_id
    idea["evaluated_at"] = datetime.now().isoformat()

    if prototype_if_go and idea.get("verdict") == "GO" and idea.get("effort") in ("S", "M"):
        spec_path = _prototype_idea(idea)
        if spec_path:
            idea["spec_file"] = spec_path
            idea["status"] = "prototyped"
        else:
            idea["status"] = "go_pending_prototype"
    elif idea.get("status") == "pending_evaluation":
        idea["status"] = f"evaluated_{idea.get('verdict', 'unknown').lower()}"

    merged: dict[str, dict] = {i["id"]: i for i in ideas if i.get("id")}
    if existing_id and existing_id in merged:
        merged[existing_id] = idea
    else:
        merged[idea["id"]] = idea
    _save_ideas(list(merged.values()))

    try:
        from skills.skill_mem0 import remember

        remember(
            f"Bibliothèque → R&D : {idea['title']} — {idea.get('verdict', '?')} "
            f"({idea.get('score', 0)}/30) — {idea.get('reasoning', '')[:200]}",
            agent_id="rnd_agent",
        )
    except Exception:
        pass

    logger.info(
        "rnd_center: idée bibliothèque développée — %s (%s, %s/30)",
        idea["title"][:50],
        idea.get("verdict"),
        idea.get("score"),
    )
    return idea


def develop_library_entries_as_rnd(
    entries: list[dict[str, Any]],
    *,
    max_count: int = 3,
) -> list[dict]:
    """Développe les fiches bibliothèque les plus pertinentes en propositions R&D scorées."""
    candidates = [
        e
        for e in entries
        if e.get("bureau") == "rd" or e.get("timing") == "now"
    ]
    developed: list[dict] = []
    for entry in candidates[:max_count]:
        try:
            developed.append(
                develop_idea_from_library(
                    title=str(entry.get("title") or ""),
                    summary=str(entry.get("summary") or ""),
                    topics=entry.get("topics") if isinstance(entry.get("topics"), list) else [],
                    source_url=str(entry.get("source_url") or ""),
                    query=str(entry.get("query") or ""),
                    bureau=str(entry.get("bureau") or "rd"),
                    library_entry_id=entry.get("id"),
                    source="bibliothèque recherche",
                )
            )
        except Exception as exc:
            logger.warning("rnd_center: develop_library_entries failed: %s", exc)
    return developed


def develop_pending_library_ideas(*, limit: int = 5) -> list[dict]:
    """Réévalue les anciennes injections bibliothèque restées en pending_evaluation."""
    ideas = _load_ideas()
    pending = [
        i
        for i in ideas
        if i.get("status") == "pending_evaluation"
        and "bibliothèque" in (i.get("source") or "").lower()
    ]
    developed: list[dict] = []
    for idea in pending[:limit]:
        try:
            developed.append(
                develop_idea_from_library(
                    title=str(idea.get("title") or ""),
                    summary=str(idea.get("description") or ""),
                    source=str(idea.get("source") or "bibliothèque"),
                    library_entry_id=idea.get("library_entry_id"),
                    existing_id=idea.get("id"),
                )
            )
        except Exception as exc:
            logger.warning("rnd_center: develop_pending_library failed: %s", exc)
    return developed


def develop_rnd_ideas_from_ceo_report(
    rnd_ideas: list[Any],
    recent_entries: list[dict[str, Any]],
    *,
    max_count: int = 3,
) -> list[dict]:
    """Développe les idées R&D du rapport CEO à partir des fiches bibliothèque."""
    developed: list[dict] = []
    entries_by_title = {str(e.get("title") or "").lower(): e for e in recent_entries}

    for item in rnd_ideas[:max_count]:
        if isinstance(item, dict):
            title = str(item.get("title") or item.get("pitch") or "").strip()
            pitch = str(item.get("pitch") or item.get("description") or title).strip()
            entry_id = item.get("source_entry_id") or item.get("library_entry_id")
            matched = next(
                (e for e in recent_entries if e.get("id") == entry_id),
                None,
            )
        else:
            title = str(item).strip()
            pitch = title
            matched = entries_by_title.get(title.lower())
            if not matched:
                for e in recent_entries:
                    et = str(e.get("title") or "").lower()
                    if et and (et in title.lower() or title.lower() in et):
                        matched = e
                        break

        if not title:
            continue

        summary = pitch
        if matched and matched.get("summary"):
            summary = f"{matched.get('summary')}\n\nSynthèse CEO : {pitch}"

        try:
            developed.append(
                develop_idea_from_library(
                    title=title,
                    summary=summary,
                    topics=(matched or {}).get("topics") if isinstance((matched or {}).get("topics"), list) else [],
                    source_url=str((matched or {}).get("source_url") or ""),
                    query=str((matched or {}).get("query") or ""),
                    bureau=str((matched or {}).get("bureau") or "rd"),
                    library_entry_id=(matched or {}).get("id"),
                    source="bibliothèque CEO",
                )
            )
        except Exception as exc:
            logger.warning("rnd_center: develop_ceo_rnd_idea failed: %s", exc)
    return developed


def submit_user_proposal(
    title: str,
    *,
    tagline: str | None = None,
    domain: str = "autre",
    why_now: str | None = None,
    sections: dict[str, str] | None = None,
    source: str = "Emilie",
) -> dict:
    """Create a structured idea record (JSON + Supabase) before dossier promotion."""
    clean_sections = {
        k: v.strip()
        for k, v in (sections or {}).items()
        if v and str(v).strip()
    }
    description_parts = [tagline] if tagline and tagline.strip() else []
    if clean_sections.get("problem"):
        description_parts.append(clean_sections["problem"])
    elif clean_sections.get("solution"):
        description_parts.append(clean_sections["solution"])
    description = "\n\n".join(description_parts) or title

    new_idea = {
        "id": f"idea_{int(datetime.now().timestamp())}",
        "title": title[:200],
        "description": description[:8000],
        "source": source,
        "status": "user_dossier",
        "score": None,
        "created_at": datetime.now().isoformat(),
        "domain": domain or "autre",
        "why_now": (why_now or "").strip()[:4000],
        "lifecycle_status": "raw",
        "user_submitted": True,
    }
    ideas = _load_ideas()
    ideas.append(new_idea)
    _save_ideas(ideas)
    logger.info("rnd_center: dossier utilisateur soumis par %s : %s", source, title[:60])
    return new_idea

