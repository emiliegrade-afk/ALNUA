"""
Promote recurrent library topics to knowledge skills (SKILL.md packs).

Triggered when learn_count >= threshold or topic has timing=now and multiple entries.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "skills" / "knowledge"
PROMOTE_LEARN_THRESHOLD = 3


def maybe_promote_topic_skill(slug: str, *, threshold: int = PROMOTE_LEARN_THRESHOLD) -> dict[str, Any] | None:
    """
    If topic is hot enough and not yet promoted, write skills/knowledge/{slug}/SKILL.md
    and record path on the catalog.
    """
    from services.topic_catalog import get_topic, mark_promoted_skill

    topic = get_topic(slug)
    if not topic:
        return None

    if topic.get("promoted_skill"):
        return {
            "ok": True,
            "already": True,
            "slug": topic.get("slug"),
            "path": topic.get("promoted_skill"),
        }

    learn_count = int(topic.get("learn_count") or 0)
    entry_count = len(topic.get("entry_ids") or [])
    hot = bool(topic.get("has_now")) and entry_count >= 2
    if learn_count < threshold and not hot:
        return None

    topic_slug = str(topic.get("slug") or slug)
    safe = re.sub(r"[^\w\-]+", "-", topic_slug).strip("-")[:60] or "topic"
    out_dir = KNOWLEDGE_DIR / safe
    out_dir.mkdir(parents=True, exist_ok=True)
    skill_path = out_dir / "SKILL.md"

    # Prefer vault digest if present
    digest_body = ""
    try:
        from services.obsidian_vault import get_vault_path

        digest_file = get_vault_path() / "library" / "_digests" / f"{topic_slug}.md"
        if digest_file.is_file():
            digest_body = digest_file.read_text(encoding="utf-8")
            if digest_body.startswith("---"):
                end = digest_body.find("\n---", 3)
                if end > 0:
                    digest_body = digest_body[end + 4 :].lstrip()
    except Exception:
        pass

    if not digest_body:
        parts = []
        for e in (topic.get("entries") or [])[:8]:
            parts.append(f"### {e.get('title')}\n\n{(e.get('digest') or e.get('summary') or '')}\n")
        digest_body = "\n".join(parts) or "_Aucune fiche._"

    titles = topic.get("titles") or []
    content = "\n".join(
        [
            "---",
            f"name: knowledge-{safe}",
            f"description: Connaissance bibliothèque ALNUA — sujet {topic_slug}",
            "type: knowledge",
            f"topic: {topic_slug}",
            "---",
            "",
            f"# Knowledge skill — {topic_slug.replace('-', ' ')}",
            "",
            "Pack de connaissances promu automatiquement depuis la bibliothèque Hub.",
            "Utilise ce skill quand la tâche touche ce sujet.",
            "",
            "## Couverture",
            "",
            f"- Slug: `{topic_slug}`",
            f"- Fiches: {entry_count}",
            f"- Learn count: {learn_count}",
            f"- Bureaux: {', '.join(topic.get('bureaus') or [])}",
            f"- Exemples: {'; '.join(titles[:5])}",
            "",
            "## Contenu",
            "",
            digest_body[:12000],
            "",
        ]
    )
    skill_path.write_text(content, encoding="utf-8")
    rel = str(skill_path.relative_to(ROOT)).replace("\\", "/")
    mark_promoted_skill(topic_slug, rel)

    try:
        from skills.skill_mem0 import remember

        remember(
            f"Knowledge skill disponible: {rel} pour le sujet bibliothèque `{topic_slug}`.",
            agent_id="coo",
            user_id="emilie",
        )
    except Exception:
        pass

    logger.info("Promoted knowledge skill for topic %s → %s", topic_slug, rel)
    return {"ok": True, "slug": topic_slug, "path": rel, "learn_count": learn_count}
