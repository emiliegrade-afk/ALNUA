"""CEO report synthesis from bureau library entries."""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from services.bureau_library_constants import BUREAU_LABELS
from services.bureau_library_store import _load_store, _save_store, _utc_now

logger = logging.getLogger(__name__)


def generate_ceo_report(*, days: int = 7) -> dict[str, Any]:
    """Synthesize library entries into Hub improvements + R&D ideas."""
    store = _load_store()
    cutoff = datetime.now(timezone.utc).timestamp() - days * 86400
    recent: list[dict[str, Any]] = []
    for e in store.get("entries", []):
        try:
            ts = datetime.fromisoformat(e.get("created_at", "").replace("Z", "+00:00")).timestamp()
            if ts >= cutoff:
                recent.append(e)
        except Exception:
            recent.append(e)

    if not recent:
        return {
            "generated_at": _utc_now(),
            "entry_count": 0,
            "hub_suggestions": [],
            "rnd_ideas": [],
            "useful_now": [],
            "kept_for_later": [],
            "markdown": "Aucune fiche récente dans la bibliothèque. Lance une recherche depuis Academy ou demande à Aria/Nadia.",
        }

    now_items = [e for e in recent if e.get("timing") == "now"]
    later_items = [e for e in recent if e.get("timing") != "now"]

    bullets = "\n".join(
        f"- [{e.get('bureau')}|{e.get('timing')}|id:{e.get('id')}] "
        f"{e.get('title')}: {e.get('summary', '')[:200]}"
        for e in recent[:40]
    )

    from agents.base import LLMClient, parse_json_response

    system = """Tu es Aria Voss, COO d'ALNUA. Tu rédiges un rapport pour Emilie (CEO).
À partir des fiches bibliothèque, propose:
- hub_suggestions: améliorations concrètes pour le Hub ALNUA (max 5)
- rnd_ideas: idées de projets R&D à développer (max 5) — chaque idée doit référencer une ou plusieurs fiches
Ne rejette aucune info — les idées "later" peuvent devenir des rnd_ideas.
JSON valide uniquement."""

    user = f"""Fiches bibliothèque ({len(recent)} sur {days} jours):

{bullets}

JSON:
{{
  "hub_suggestions": ["..."],
  "rnd_ideas": [
    {{
      "title": "Nom court du concept produit",
      "pitch": "2-3 phrases — problème, solution, pourquoi ALNUA",
      "source_entry_id": "uuid de la fiche source si identifiable, sinon vide"
    }}
  ],
  "executive_summary": "2-3 phrases pour Emilie"
}}"""

    hub_suggestions: list[str] = []
    rnd_ideas: list[dict[str, Any] | str] = []
    executive_summary = ""

    try:
        llm = LLMClient()
        raw = llm.complete(system, user, agent_id="coo", temperature=0.3)
        parsed = parse_json_response(raw)
        if isinstance(parsed, dict):
            hub_suggestions = [str(x) for x in parsed.get("hub_suggestions", [])[:5]]
            raw_rnd = parsed.get("rnd_ideas", [])[:5]
            rnd_ideas = []
            for item in raw_rnd:
                if isinstance(item, dict):
                    rnd_ideas.append(item)
                elif item:
                    rnd_ideas.append({"title": str(item), "pitch": str(item)})
            executive_summary = str(parsed.get("executive_summary") or "")
    except Exception as exc:
        logger.warning("ceo report LLM failed: %s", exc)
        executive_summary = f"{len(now_items)} fiche(s) utiles maintenant, {len(later_items)} à garder."

    markdown = (
        f"## Rapport bibliothèque ALNUA\n\n"
        f"{executive_summary}\n\n"
        f"### Utile maintenant ({len(now_items)})\n"
        + "\n".join(
            f"- **{e.get('title')}** ({BUREAU_LABELS.get(e.get('bureau', ''), e.get('bureau'))})"
            for e in now_items[:8]
        )
        + f"\n\n### À garder pour plus tard ({len(later_items)})\n"
        + "\n".join(f"- {e.get('title')}" for e in later_items[:8])
        + "\n\n### Suggestions Hub\n"
        + "\n".join(f"- {s}" for s in hub_suggestions)
        + "\n\n### Idées R&D\n"
        + "\n".join(
            f"- **{(i.get('title') if isinstance(i, dict) else str(i))}**"
            + (
                f" — {(i.get('pitch') or '')[:120]}"
                if isinstance(i, dict) and i.get("pitch")
                else ""
            )
            for i in rnd_ideas
        )
    )

    rnd_developed: list[dict[str, Any]] = []
    try:
        from agents.rnd_center import (
            develop_pending_library_ideas,
            develop_rnd_ideas_from_ceo_report,
        )

        develop_pending_library_ideas(limit=5)
        rnd_developed = develop_rnd_ideas_from_ceo_report(rnd_ideas, recent, max_count=3)
    except Exception as exc:
        logger.warning("ceo report → R&D develop failed: %s", exc)

    report = {
        "id": str(uuid.uuid4()),
        "generated_at": _utc_now(),
        "entry_count": len(recent),
        "hub_suggestions": hub_suggestions,
        "rnd_ideas": rnd_ideas,
        "rnd_developed": len(rnd_developed),
        "rnd_proposals": [
            {
                "id": d.get("id"),
                "title": d.get("title"),
                "verdict": d.get("verdict"),
                "score": d.get("score"),
            }
            for d in rnd_developed
        ],
        "useful_now": [e.get("title") for e in now_items[:10]],
        "kept_for_later": [e.get("title") for e in later_items[:10]],
        "executive_summary": executive_summary,
        "markdown": markdown,
    }

    if rnd_developed:
        markdown += (
            "\n\n### Propositions R&D développées\n"
            + "\n".join(
                f"- **{d.get('title')}** — {d.get('verdict', '?')} "
                f"({d.get('score', '?')}/30)"
                for d in rnd_developed
            )
        )
        report["markdown"] = markdown

    store.setdefault("reports", []).append(report)
    store["reports"] = store["reports"][-20:]
    _save_store(store)

    return report
