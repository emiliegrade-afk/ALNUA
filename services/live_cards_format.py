"""Structured fences for Live result cards (list / image / draft). Never HTML."""

from __future__ import annotations

import json
from typing import Any


def fence(kind: str, payload: dict[str, Any], *, lead: str = "") -> str:
    body = json.dumps(payload, ensure_ascii=False)
    head = f"{lead.strip()}\n\n" if lead.strip() else ""
    return f"{head}```{kind}\n{body}\n```"


def list_card(title: str, items: list[str], *, lead: str = "") -> str:
    clean = [str(item).strip()[:220] for item in items if str(item).strip()]
    return fence("list", {"title": title[:120], "items": clean[:12]}, lead=lead or title)


def image_card(
    *,
    title: str,
    src: str,
    credit: str,
    href: str = "",
    lead: str = "",
) -> str:
    return fence(
        "image",
        {
            "title": title[:120],
            "src": src[:400],
            "credit": credit[:200],
            "href": href[:400],
        },
        lead=lead or title,
    )


def draft_card(
    *,
    kind: str,
    title: str,
    body: str,
    draft_id: str,
    lead: str = "",
) -> str:
    return fence(
        "draft",
        {
            "kind": kind[:32],
            "title": title[:160],
            "body": body[:4000],
            "draft_id": draft_id[:64],
        },
        lead=lead or title,
    )
