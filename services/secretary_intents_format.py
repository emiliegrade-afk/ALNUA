"""Format structured secretary JSON output for chat surfaces."""

from __future__ import annotations

from typing import Any


def format_json_reply(data: dict[str, Any], *, kind: str) -> str:
    """Turn structured secretary output into chat-friendly text."""
    if kind == "email":
        return (
            f"**Objet :** {data.get('subject', '—')}\n\n"
            f"{data.get('body', '')}\n\n"
            f"_Envoi suggéré : {data.get('suggested_send_time', 'matin')}_"
        )
    if kind == "contract":
        articles = data.get("articles") or []
        body = data.get("preamble", "")
        if articles:
            body += "\n\n" + "\n\n".join(
                f"**Art. {a.get('number')} — {a.get('title')}**\n{a.get('content', '')}"
                for a in articles[:4]
            )
            if len(articles) > 4:
                body += f"\n\n_… et {len(articles) - 4} articles supplémentaires (voir Hub)._"
        return f"**{data.get('title', 'Contrat')}**\n\n{body}"
    if kind == "meeting":
        agenda = data.get("agenda") or []
        items = "\n".join(
            f"• {a.get('time', '?')} ({a.get('duration', '?')} min) — {a.get('item', '')}"
            for a in agenda[:8]
        )
        return (
            f"**{data.get('title', 'Réunion')}**\n"
            f"{data.get('objective', '')}\n\n"
            f"**Ordre du jour :**\n{items}"
        )
    if kind == "notes":
        actions = data.get("action_items") or []
        act = "\n".join(
            f"• {a.get('action', '')} → {a.get('owner', '?')} ({a.get('deadline', '?')})"
            for a in actions[:6]
        )
        return (
            f"**{data.get('title', 'Compte rendu')}**\n\n"
            f"{data.get('summary', '')}\n\n"
            f"**Actions :**\n{act or '—'}"
        )
    return str(data)
