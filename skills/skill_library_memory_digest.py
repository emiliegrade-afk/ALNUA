"""Library memory — topic digest builders."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

DIGEST_MIN_ENTRIES = 2


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def concat_digest(slug: str, entries: list[dict[str, Any]]) -> str:
    lines = [
        "---",
        "type: library_digest",
        f"topic: {slug}",
        f'hub_synced_at: "{utc_now()}"',
        "---",
        "",
        f"# Digest — {slug.replace('-', ' ')}",
        "",
        f"_{len(entries)} fiches consolidées (concat)_",
        "",
    ]
    for e in entries:
        title = e.get("title") or "Sans titre"
        body = (e.get("digest") or e.get("summary") or "").strip()
        lines.append(f"## {title}")
        lines.append("")
        lines.append(body or "_vide_")
        lines.append("")
        url = (e.get("source_url") or "").strip()
        if url:
            lines.append(f"Source: {url}")
            lines.append("")
    return "\n".join(lines)


def llm_digest(slug: str, entries: list[dict[str, Any]]) -> str | None:
    try:
        from agents.base import LLMClient

        cards = []
        for e in entries:
            body = (e.get("digest") or e.get("summary") or "")[:2000]
            cards.append(
                f"- {e.get('title')}\n  timing={e.get('timing')} bureau={e.get('bureau')}\n  {body}"
            )
        system = (
            "Tu es l'archiviste ALNUA. Synthétise des fiches bibliothèque en un digest "
            "actionnable pour des agents IA. Garde les faits, chiffres, outils, dates. "
            "Pas de blabla. Markdown clair avec titres ##."
        )
        user = (
            f"Sujet: {slug}\n\nFiches:\n"
            + "\n".join(cards)
            + "\n\nProduis un digest structuré (max ~800 mots) : points clés, "
            "quand appliquer, pièges, sources à retenir."
        )
        llm = LLMClient()
        raw = llm.complete(system, user, agent_id="coo", temperature=0.2, max_tokens=2000)
        if not raw or not str(raw).strip():
            return None
        content = str(raw).strip()
        return (
            "---\n"
            f"type: library_digest\n"
            f"topic: {slug}\n"
            f'hub_synced_at: "{utc_now()}"\n'
            "---\n\n"
            f"# Digest — {slug.replace('-', ' ')}\n\n"
            f"_Synthèse LLM de {len(entries)} fiches_\n\n"
            f"{content}\n"
        )
    except Exception as exc:
        logger.warning("ensure_topic_digest LLM failed for %s: %s", slug, exc)
        return None


def build_topic_digest(
    slug: str,
    *,
    force: bool = False,
    max_entries: int = 12,
) -> dict[str, Any]:
    """Build or refresh a vault digest note synthesizing library entries for a topic."""
    from services.obsidian_vault import ensure_vault_layout, get_vault_path
    from services.topic_catalog import get_topic

    topic = get_topic(slug)
    if not topic:
        return {"ok": False, "error": "topic_not_found", "slug": slug}

    topic_slug = topic.get("slug") or slug
    vault = get_vault_path()
    ensure_vault_layout(vault)
    digest_rel = f"library/_digests/{topic_slug}.md"
    digest_path = vault / digest_rel

    if digest_path.is_file() and not force:
        return {
            "ok": True,
            "slug": topic_slug,
            "path": digest_rel,
            "cached": True,
            "content": digest_path.read_text(encoding="utf-8"),
        }

    entries = list(topic.get("entries") or [])[:max_entries]
    if not entries:
        return {"ok": False, "error": "no_entries", "slug": topic_slug}

    if len(entries) < DIGEST_MIN_ENTRIES:
        body = concat_digest(topic_slug, entries)
        digest_path.write_text(body, encoding="utf-8")
        return {
            "ok": True,
            "slug": topic_slug,
            "path": digest_rel,
            "cached": False,
            "mode": "concat",
            "content": body,
        }

    body = llm_digest(topic_slug, entries) or concat_digest(topic_slug, entries)
    digest_path.write_text(body, encoding="utf-8")
    return {
        "ok": True,
        "slug": topic_slug,
        "path": digest_rel,
        "cached": False,
        "mode": "llm" if "Synthèse" in body or "Digest" in body else "concat",
        "content": body,
    }
