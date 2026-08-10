"""Sentry webhook parsing and signature verification."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from pydantic import BaseModel, Field


class SentryIngestEvent(BaseModel):
    fingerprint: str
    title: str
    message: str
    level: str = "error"
    culprit: str = ""
    permalink: str = ""
    environment: str = "production"
    project_slug: str = ""
    platform: str = ""
    stacktrace: str = ""
    tags: dict[str, str] = Field(default_factory=dict)
    event_id: str = ""
    issue_id: str = ""


def verify_sentry_signature(
    body: bytes,
    signature: str | None,
    secret: str,
    *,
    allow_unsigned: bool = False,
) -> bool:
    """HMAC-SHA256 verification (Sentry-Hook-Signature header)."""
    if not secret.strip():
        return allow_unsigned
    if not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.strip())


def _tags_list_to_dict(tags: Any) -> dict[str, str]:
    if isinstance(tags, dict):
        return {str(k): str(v) for k, v in tags.items()}
    if isinstance(tags, list):
        out: dict[str, str] = {}
        for item in tags:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                out[str(item[0])] = str(item[1])
        return out
    return {}


def _extract_stacktrace(event: dict[str, Any]) -> str:
    entries = event.get("entries") or []
    for entry in entries:
        if entry.get("type") != "exception":
            continue
        values = (entry.get("data") or {}).get("values") or []
        lines: list[str] = []
        for exc in values[:3]:
            etype = exc.get("type", "Error")
            evalue = exc.get("value", "")
            lines.append(f"{etype}: {evalue}")
            for frame in ((exc.get("stacktrace") or {}).get("frames") or [])[-8:]:
                fn = frame.get("filename", "?")
                func = frame.get("function", "?")
                line = frame.get("lineNo", "?")
                lines.append(f"  at {func} ({fn}:{line})")
        return "\n".join(lines)[:4000]
    exception = event.get("exception") or {}
    if isinstance(exception, dict):
        values = exception.get("values") or []
        if values:
            v0 = values[0]
            return f"{v0.get('type', 'Error')}: {v0.get('value', '')}"[:2000]
    return str(event.get("message") or "")[:2000]


def parse_sentry_webhook(payload: dict[str, Any]) -> SentryIngestEvent | None:
    """
    Support Sentry Issue Alert webhooks and direct event payloads.
    Returns None if payload is not actionable (e.g. resolved action).
    """
    action = str(payload.get("action") or "").lower()
    if action in {"resolved", "archived", "ignored"}:
        return None

    data = payload.get("data") or {}
    issue = data.get("issue") or payload.get("issue") or {}
    event = data.get("event") or payload.get("event") or payload

    title = (
        issue.get("title")
        or event.get("title")
        or event.get("message")
        or payload.get("message")
        or "Sentry alert"
    )
    title = str(title).strip()[:200]
    if not title:
        return None

    tags = _tags_list_to_dict(event.get("tags") or payload.get("tags"))
    environment = (
        tags.get("environment")
        or event.get("environment")
        or payload.get("environment")
        or "production"
    )
    project_slug = (
        tags.get("project")
        or (payload.get("project") or {}).get("slug")
        or (issue.get("project") or {}).get("slug")
        or ""
    )
    culprit = str(issue.get("culprit") or event.get("culprit") or "")[:300]
    permalink = str(
        issue.get("permalink")
        or issue.get("web_url")
        or event.get("url")
        or ""
    )
    level = str(issue.get("level") or event.get("level") or "error").lower()
    platform = str(event.get("platform") or "")
    event_id = str(event.get("event_id") or event.get("id") or "")
    issue_id = str(issue.get("id") or "")

    message = str(
        event.get("message")
        or (issue.get("metadata") or {}).get("value")
        or title
    )[:2000]
    stacktrace = _extract_stacktrace(event if isinstance(event, dict) else {})

    fingerprint_src = "|".join(
        filter(
            None,
            [
                project_slug,
                title,
                culprit,
                environment,
                issue_id or event_id,
            ],
        )
    )
    fingerprint = hashlib.sha256(fingerprint_src.encode("utf-8")).hexdigest()[:24]

    return SentryIngestEvent(
        fingerprint=fingerprint,
        title=title,
        message=message,
        level=level,
        culprit=culprit,
        permalink=permalink,
        environment=str(environment),
        project_slug=str(project_slug),
        platform=platform,
        stacktrace=stacktrace,
        tags=tags,
        event_id=event_id,
        issue_id=issue_id,
    )
