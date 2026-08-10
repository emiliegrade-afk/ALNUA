"""Async web research pipeline for bureau library."""
from __future__ import annotations

import logging
import threading
from typing import Any

from services.bureau_library_constants import BUREAU_LABELS
from services.bureau_library_extract import _extract_entries_from_research

logger = logging.getLogger(__name__)


def _dispatch_research_notify(chat_id: int, query: str, result: dict[str, Any]) -> None:
    """Call notify via façade so callers/tests can monkeypatch one import path."""
    from services import bureau_library as bl

    bl._notify_research_complete(chat_id, query, result)


def _notify_research_complete_impl(
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
                _dispatch_research_notify(notify_chat_id, query, final)
        except Exception as exc:
            logger.exception("bureau research failed")
            err = {"success": False, "error": str(exc), "query": query}
            result_holder.update(err)
            if notify_chat_id is not None:
                _dispatch_research_notify(notify_chat_id, query, err)

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
