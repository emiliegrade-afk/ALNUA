"""
Bureau library — research results stored per department, nothing discarded.

Each entry is tagged ``now`` (actionable today) or ``later`` (keep for future).
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

Timing = Literal["now", "later"]
BureauId = Literal[
    "hub",
    "secretary",
    "app",
    "gaming",
    "robo",
    "marketing",
    "rd",
    "finances",
    "analytics",
    "academy",
]

ROOT = Path(__file__).resolve().parent.parent
LIBRARY_FILE = ROOT / "data" / "bureau_library.json"

BUREAU_LABELS: dict[str, str] = {
    "hub": "Direction",
    "secretary": "Secrétariat",
    "app": "App Dev",
    "gaming": "Gaming Studio",
    "robo": "Robotics Lab",
    "marketing": "Marketing & Contenu",
    "rd": "R&D Lab",
    "finances": "Finance",
    "analytics": "Analytics",
    "academy": "Academy",
}

AGENT_TO_BUREAU: dict[str, str] = {
    "coo": "hub",
    "spec": "hub",
    "qa": "hub",
    "pm": "hub",
    "secretary": "secretary",
    "dev_app": "app",
    "dev_frontend": "hub",
    "dev_backend": "hub",
    "dev_integrator": "hub",
    "dev_gaming": "gaming",
    "content_app": "app",
    "content_gaming": "gaming",
    "content_robo": "robo",
    "content_company": "hub",
    "content": "hub",
    "dev_backend": "app",
    "game_director": "gaming",
    "dev_gaming": "gaming",
    "level_designer": "gaming",
    "brainstorm": "rd",
    "rnd_agent": "rd",
    "marketing": "marketing",
    "marketing_agent": "marketing",
    "content": "marketing",
    "content_agent": "marketing",
    "hardware": "robo",
    "hardware_agent": "robo",
    "embedded_dev": "robo",
    "accounting": "finances",
    "accountant_agent": "finances",
    "controller": "finances",
    "analyst_business": "analytics",
    "analyst_data": "analytics",
}

VALID_BUREAUS = frozenset(BUREAU_LABELS)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_store() -> dict[str, Any]:
    return {"version": 1, "entries": [], "reports": [], "archives": []}


def _load_store() -> dict[str, Any]:
    if not LIBRARY_FILE.exists():
        return _empty_store()
    try:
        data = json.loads(LIBRARY_FILE.read_text(encoding="utf-8"))
        data.setdefault("entries", [])
        data.setdefault("reports", [])
        data.setdefault("archives", [])
        return data
    except Exception as exc:
        logger.warning("bureau_library load failed: %s", exc)
        return _empty_store()


def _save_store(data: dict[str, Any]) -> None:
    LIBRARY_FILE.parent.mkdir(parents=True, exist_ok=True)
    LIBRARY_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def bureau_for_agent(agent_id: str | None) -> str:
    if not agent_id:
        return "hub"
    return AGENT_TO_BUREAU.get(agent_id, AGENT_TO_BUREAU.get(agent_id.replace("_agent", ""), "hub"))


def add_entry(
    *,
    bureau: str,
    title: str,
    summary: str,
    timing: Timing = "later",
    source_url: str = "",
    source_title: str = "",
    topics: list[str] | None = None,
    agent_id: str = "",
    requested_by: str = "ceo",
    query: str = "",
    digest: str = "",
) -> dict[str, Any]:
    bureau = bureau if bureau in VALID_BUREAUS else "hub"
    entry = {
        "id": str(uuid.uuid4()),
        "bureau": bureau,
        "title": title[:300],
        "summary": summary[:4000],
        "digest": (digest or "")[:12000],
        "timing": timing if timing in ("now", "later") else "later",
        "source_url": source_url[:2000],
        "source_title": source_title[:300],
        "topics": (topics or [])[:12],
        "agent_id": agent_id,
        "requested_by": requested_by,
        "query": query[:500],
        "created_at": _utc_now(),
    }
    store = _load_store()
    store["entries"].append(entry)
    _save_store(store)

    try:
        from services.team_enrichment import fanout_library_entry

        fanout_library_entry(entry, distill_lessons=entry["timing"] == "now")
    except Exception as exc:
        logger.debug("library fanout skipped: %s", exc)

    try:
        from services.library_vault_export import export_entry_to_vault

        export_entry_to_vault(entry, update_catalog=True)
    except Exception as exc:
        logger.debug("library vault export skipped: %s", exc)

    return entry


def list_entries(
    *,
    bureau: str | None = None,
    timing: Timing | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    store = _load_store()
    entries = list(store.get("entries", []))
    entries.sort(key=lambda e: e.get("created_at", ""), reverse=True)

    if bureau and bureau in VALID_BUREAUS:
        entries = [e for e in entries if e.get("bureau") == bureau]
    if timing in ("now", "later"):
        entries = [e for e in entries if e.get("timing") == timing]

    total = len(entries)
    page = entries[offset : offset + limit]
    counts: dict[str, int] = {b: 0 for b in BUREAU_LABELS}
    timing_counts = {"now": 0, "later": 0}
    for e in store.get("entries", []):
        b = e.get("bureau", "hub")
        if b in counts:
            counts[b] += 1
        t = e.get("timing", "later")
        if t in timing_counts:
            timing_counts[t] += 1

    return {
        "entries": page,
        "total": total,
        "counts_by_bureau": counts,
        "counts_by_timing": timing_counts,
    }


def get_bureaus_meta() -> list[dict[str, Any]]:
    counts = list_entries(limit=0)["counts_by_bureau"]
    return [
        {"id": bid, "label": label, "entry_count": counts.get(bid, 0)}
        for bid, label in BUREAU_LABELS.items()
    ]


def _extract_entries_from_research(
    query: str,
    raw_results: list[dict[str, Any]],
    requested_by: str,
) -> list[dict[str, Any]]:
    """LLM turns search hits into library entries — keep everything, tag now/later."""
    if not raw_results:
        return []

    from agents.base import parse_json_response

    results_text = "\n\n".join(
        f"Titre: {r.get('title', '')}\nURL: {r.get('url', '')}\n"
        f"Contenu: {(r.get('content') or '')[:500]}"
        for r in raw_results[:12]
    )

    bureau_list = ", ".join(f"{k}={v}" for k, v in BUREAU_LABELS.items())

    system = """Tu es l'archiviste de la bibliothèque ALNUA Hub.
À partir de résultats de recherche web, tu crées des fiches pour les bureaux de l'entreprise.

RÈGLES ABSOLUES:
- Ne jette AUCUNE information utile — tout va dans la bibliothèque.
- timing "now" = applicable tout de suite au Hub ou à un projet en cours.
- timing "later" = pas prioritaire aujourd'hui mais à conserver pour plus tard.
- Si tu hésites, mets "later" — jamais de suppression.
- summary = 2-4 phrases courtes pour l'UI / scan rapide.
- digest = synthèse riche (faits, chiffres, outils, dates, quand appliquer) — 150 à 400 mots si le contenu le permet.
- Réponds en JSON valide uniquement."""

    user = f"""Recherche demandée par Emilie (CEO): {query}

Bureaux possibles: {bureau_list}

Résultats web:
{results_text}

Réponds avec ce JSON:
{{
  "entries": [
    {{
      "bureau": "app",
      "title": "titre court",
      "summary": "2-4 phrases — ce que c'est et quand ça pourrait servir",
      "digest": "synthèse riche actionnable (150-400 mots) — faits clés, chiffres, outils, pièges",
      "timing": "now|later",
      "source_url": "url ou vide",
      "source_title": "titre source",
      "topics": ["IA", "UI"],
      "agent_id": "dev_app"
    }}
  ]
}}

Minimum 1 entrée si les résultats contiennent du contenu. Maximum 8 entrées."""

    try:
        from agents.base import LLMClient

        llm = LLMClient()
        raw = llm.complete(system, user, agent_id="coo", temperature=0.2)
        parsed = parse_json_response(raw)
        items = parsed.get("entries") if isinstance(parsed, dict) else []
        if not isinstance(items, list):
            return []
    except Exception as exc:
        logger.warning("library extract LLM failed: %s", exc)
        items = []

    saved: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        summary = str(item.get("summary") or "").strip()
        digest = str(item.get("digest") or "").strip()
        if not title and not summary and not digest:
            continue
        if not title:
            title = (summary or digest)[:80]
        if not summary and digest:
            summary = digest[:400]
        bureau = str(item.get("bureau") or "hub")
        agent_id = str(item.get("agent_id") or "")
        if not agent_id:
            agent_id = _default_agent_for_bureau(bureau)
        timing = item.get("timing", "later")
        if timing not in ("now", "later"):
            timing = "later"
        saved.append(
            add_entry(
                bureau=bureau,
                title=title,
                summary=summary or title,
                digest=digest,
                timing=timing,
                source_url=str(item.get("source_url") or ""),
                source_title=str(item.get("source_title") or ""),
                topics=item.get("topics") if isinstance(item.get("topics"), list) else [],
                agent_id=agent_id,
                requested_by=requested_by,
                query=query,
            )
        )

    if not saved and raw_results:
        fallback = raw_results[0]
        saved.append(
            add_entry(
                bureau="hub",
                title=str(fallback.get("title") or query)[:300],
                summary=str(fallback.get("content") or query)[:2000],
                timing="later",
                source_url=str(fallback.get("url") or ""),
                source_title=str(fallback.get("title") or ""),
                topics=[query[:80]],
                agent_id="coo",
                requested_by=requested_by,
                query=query,
            )
        )

    return saved


def _default_agent_for_bureau(bureau: str) -> str:
    defaults = {
        "hub": "coo",
        "secretary": "secretary",
        "app": "content_app",
        "gaming": "content_gaming",
        "robo": "content_robo",
        "marketing": "marketing",
        "rd": "rnd_agent",
        "finances": "accounting",
        "analytics": "analyst_business",
        "academy": "dev_app",
    }
    return defaults.get(bureau, "coo")


def _notify_research_complete(
    chat_id: int,
    query: str,
    result: dict[str, Any],
) -> None:
    """Telegram follow-up when async bureau research finishes."""
    try:
        from skills.skill_telegram_notify import notify_telegram

        if not result.get("success", True):
            notify_telegram(
                f"❌ Recherche bibliothèque échouée pour « {query[:80]} » : "
                f"{result.get('error', 'erreur inconnue')}",
                chat_id=chat_id,
            )
            return
        n = int(result.get("entries_saved") or 0)
        msg = (
            f"📚 **Recherche terminée** — « {query[:120]} »\n\n"
            f"**{n}** fiche(s) archivée(s) dans la bibliothèque (rien supprimé)."
        )
        rnd_n = int(result.get("rnd_developed") or 0)
        if rnd_n:
            msg += f"\n\n🧪 {rnd_n} concept(s) R&D développé(s) et scorés."
        notify_telegram(msg, chat_id=chat_id)
    except Exception:
        logger.warning("bureau research telegram notify failed", exc_info=True)


def run_bureau_research(
    query: str,
    *,
    bureaus: list[str] | None = None,
    requested_by: str = "ceo",
    blocking: bool = False,
    notify_chat_id: int | None = None,
) -> dict[str, Any]:
    """Run web research and archive all findings in bureau library."""

    def _run() -> dict[str, Any]:
        from skills.skill_web_research import _search

        search_queries = [query]
        if bureaus:
            for b in bureaus[:3]:
                label = BUREAU_LABELS.get(b, b)
                search_queries.append(f"{query} {label}")

        all_results: list[dict[str, Any]] = []
        seen_urls: set[str] = set()
        for sq in search_queries[:4]:
            for hit in _search(sq, max_results=5):
                url = str(hit.get("url") or "")
                if url and url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                all_results.append(hit)

        try:
            from services.trend_monitor import aggregate_trends

            for item in aggregate_trends(sources=["hn", "github"], topics=[query])[:5]:
                url = item.url
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                all_results.append(
                    {
                        "title": item.title,
                        "url": url,
                        "content": f"[{item.source}] score={item.score}",
                    }
                )
        except Exception:
            pass

        entries = _extract_entries_from_research(query, all_results, requested_by)

        rnd_developed: list[dict[str, Any]] = []
        try:
            from agents.rnd_center import develop_library_entries_as_rnd

            rnd_developed = develop_library_entries_as_rnd(entries, max_count=3)
        except Exception as exc:
            logger.warning("library research → R&D develop skipped: %s", exc)

        message = (
            f"{len(entries)} fiche(s) archivée(s) dans la bibliothèque "
            f"— rien n'a été supprimé."
        )
        if rnd_developed:
            titles = ", ".join(d.get("title", "?")[:40] for d in rnd_developed[:3])
            message += (
                f" {len(rnd_developed)} concept(s) R&D développé(s) et scoré(s) : {titles}."
            )

        return {
            "success": True,
            "query": query,
            "entries_saved": len(entries),
            "entries": entries,
            "rnd_developed": len(rnd_developed),
            "rnd_ideas": rnd_developed,
            "message": message,
        }

    if blocking:
        return _run()

    result_holder: dict[str, Any] = {"status": "started"}

    def _thread() -> None:
        try:
            final = _run()
            result_holder.update(final)
            if notify_chat_id is not None:
                _notify_research_complete(notify_chat_id, query, final)
        except Exception as exc:
            logger.exception("bureau research failed")
            err = {"success": False, "error": str(exc), "query": query}
            result_holder.update(err)
            if notify_chat_id is not None:
                _notify_research_complete(notify_chat_id, query, err)

    threading.Thread(target=_thread, daemon=True).start()
    return {
        "success": True,
        "status": "started",
        "query": query,
        "message": (
            f"Recherche lancée sur « {query} » — "
            + (
                "tu recevras le bilan ici dans ~1-3 min."
                if notify_chat_id is not None
                else "les fiches apparaîtront dans la bibliothèque sous peu."
            )
        ),
    }


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
        + "\n".join(f"- **{e.get('title')}** ({BUREAU_LABELS.get(e.get('bureau', ''), e.get('bureau'))})" for e in now_items[:8])
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
