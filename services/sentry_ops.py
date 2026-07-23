"""Sentry production alerts → error journal + GitHub hotfix issues (Phase 4)."""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
from pydantic import BaseModel, Field

from config.github_repos import get_target_by_slug, resolve_target
from skills.skill_error_journal import log_error

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
_DEDUP_PATH = Path(__file__).resolve().parent.parent / "data" / "sentry_ingest.json"
_ISSUE_PREFIX = "[HOTFIX]"


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


def resolve_repo_slug_from_sentry(event: SentryIngestEvent) -> str:
    """Map Sentry project/tags → hub repo slug."""
    raw_map = os.getenv("SENTRY_REPO_MAP", "").strip()
    if raw_map:
        try:
            mapping = json.loads(raw_map)
            for key in (
                event.project_slug,
                event.tags.get("repo_slug"),
                event.tags.get("project"),
            ):
                if key and key in mapping:
                    return str(mapping[key])
        except json.JSONDecodeError:
            pass

    haystack = " ".join(
        [
            event.project_slug,
            event.title,
            event.culprit,
            event.tags.get("project", ""),
        ]
    ).lower()

    if any(k in haystack for k in ("hub", "alnua")):
        if get_target_by_slug("hub"):
            return "hub"
    if "academy" in haystack and get_target_by_slug("academy"):
        return "academy"
    if get_target_by_slug("hub"):
        return "hub"
    if get_target_by_slug("academy"):
        return "academy"
    return "hub"


def resolve_agent_from_sentry(event: SentryIngestEvent, repo_slug: str) -> str:
    if repo_slug in ("academy",):
        return "dev_app"
    platform = (event.platform or "").lower()
    if platform in ("python", "fastapi"):
        return "dev_backend"
    return "dev_backend"


def _load_dedup() -> dict[str, Any]:
    if not _DEDUP_PATH.exists():
        return {"fingerprints": {}, "recent": []}
    try:
        return json.loads(_DEDUP_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"fingerprints": {}, "recent": []}


def _save_dedup(data: dict[str, Any]) -> None:
    _DEDUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    _DEDUP_PATH.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _github_headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise ValueError("GITHUB_TOKEN manquant")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _issue_title(event: SentryIngestEvent) -> str:
    base = event.title.strip()
    if base.upper().startswith(_ISSUE_PREFIX):
        return base[:120]
    short = re.sub(r"\s+", " ", base)[:80]
    return f"{_ISSUE_PREFIX} [sentry] {short}"


def format_hotfix_issue_body(
    event: SentryIngestEvent,
    *,
    repo_slug: str,
    github_repo: str,
    journal_id: str | None,
) -> str:
    lines = [
        "## Description",
        f"Erreur production Sentry — **{event.level}**",
        "",
        event.message,
        "",
        "## Stack",
        _stack_hint(event, repo_slug),
        "",
        "## Contexte Sentry",
        f"- Environment : `{event.environment}`",
        f"- Project : `{event.project_slug or '—'}`",
        f"- Culprit : `{event.culprit or '—'}`",
        f"- Fingerprint : `{event.fingerprint}`",
    ]
    if event.permalink:
        lines.append(f"- Lien : {event.permalink}")
    if journal_id:
        lines.append(f"- Error journal : `{journal_id}`")
    lines.extend(["", "## Stacktrace", "```", event.stacktrace or "(non disponible)", "```"])
    lines.extend(
        [
            "",
            "## Fichiers à modifier",
            "- _(à identifier par l'agent — voir culprit / stacktrace)_",
            "",
            "## Tests",
            "- Reproduire le scénario + test de non-régression",
            "",
            "## Contexte additionnel",
            f"- Repo : `{github_repo}` (`{repo_slug}`)",
            "- Source : Sentry webhook → fix_pipeline",
            "- Priorité : hotfix production",
        ]
    )
    return "\n".join(lines)


def _stack_hint(event: SentryIngestEvent, repo_slug: str) -> str:
    platform = (event.platform or "").lower()
    if platform in ("javascript", "node", "react-native"):
        return "react_native_expo"
    if repo_slug == "hub":
        return "python_fastapi"
    if repo_slug in ("academy",):
        return "react_native_expo"
    return "python_fastapi"


def create_hotfix_github_issue(
    event: SentryIngestEvent,
    *,
    repo_slug: str,
    journal_id: str | None,
    mark_agent_ready: bool = True,
) -> dict[str, Any]:
    target = resolve_target(repo_slug=repo_slug)
    labels = ["sentry", "hotfix", "prod", f"severity-{event.level}"]
    if mark_agent_ready:
        labels.append("agent-ready")

    body = format_hotfix_issue_body(
        event,
        repo_slug=repo_slug,
        github_repo=target.github_repo,
        journal_id=journal_id,
    )
    url = f"{GITHUB_API}/repos/{target.github_repo}/issues"
    payload = {"title": _issue_title(event), "body": body, "labels": labels}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, headers=_github_headers(), json=payload)
        resp.raise_for_status()
        issue = resp.json()
    return {
        "number": issue["number"],
        "title": issue["title"],
        "url": issue.get("html_url"),
        "repo_slug": repo_slug,
        "github_repo": target.github_repo,
    }


def ingest_sentry_event(
    event: SentryIngestEvent,
    *,
    create_issue: bool = True,
    dedup_hours: int = 24,
) -> dict[str, Any]:
    """
    Full ingest: dedup → error journal → optional GitHub hotfix issue.
    bug_watchdog picks up journal entries automatically.
    """
    dedup = _load_dedup()
    fingerprints = dedup.setdefault("fingerprints", {})
    existing = fingerprints.get(event.fingerprint)

    now = datetime.now(timezone.utc)
    if existing:
        last_seen = existing.get("last_seen", "")
        try:
            last_dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
            age_h = (now - last_dt).total_seconds() / 3600
        except ValueError:
            age_h = dedup_hours + 1
        existing["count"] = int(existing.get("count") or 0) + 1
        existing["last_seen"] = now.isoformat()
        _save_dedup(dedup)
        if age_h < dedup_hours:
            return {
                "action": "dedup_skipped",
                "fingerprint": event.fingerprint,
                "occurrences": existing["count"],
                "github_issue": existing.get("github_issue"),
                "journal_id": existing.get("journal_id"),
            }

    repo_slug = resolve_repo_slug_from_sentry(event)
    agent_name = resolve_agent_from_sentry(event, repo_slug)

    context_parts = [
        f"Sentry {event.level} — {event.environment}",
        f"project={event.project_slug}",
        f"culprit={event.culprit}",
        f"fingerprint={event.fingerprint}",
    ]
    if event.permalink:
        context_parts.append(f"url={event.permalink}")
    if event.stacktrace:
        context_parts.append(f"stack:\n{event.stacktrace[:1500]}")

    journal_id = log_error(
        agent_name=agent_name,
        error_type=f"sentry_{event.level}",
        error_message=event.message or event.title,
        context="\n".join(context_parts),
        task_id=event.issue_id or event.event_id or event.fingerprint,
    )

    github_issue: dict[str, Any] | None = None
    if create_issue and os.getenv("SENTRY_AUTO_ISSUE", "true").lower() in ("1", "true", "yes"):
        try:
            github_issue = create_hotfix_github_issue(
                event,
                repo_slug=repo_slug,
                journal_id=journal_id,
                mark_agent_ready=event.level in ("error", "fatal", "critical"),
            )
        except Exception as exc:
            logger.warning("sentry hotfix issue failed: %s", exc)

    fingerprints[event.fingerprint] = {
        "last_seen": now.isoformat(),
        "first_seen": (existing or {}).get("first_seen") or now.isoformat(),
        "count": 1 if not existing else int(existing.get("count") or 0),
        "title": event.title,
        "journal_id": journal_id,
        "github_issue": github_issue,
        "repo_slug": repo_slug,
    }
    recent = dedup.setdefault("recent", [])
    recent.insert(
        0,
        {
            "fingerprint": event.fingerprint,
            "title": event.title,
            "at": now.isoformat(),
            "journal_id": journal_id,
            "issue_number": (github_issue or {}).get("number"),
        },
    )
    dedup["recent"] = recent[:50]
    _save_dedup(dedup)

    return {
        "action": "ingested",
        "fingerprint": event.fingerprint,
        "journal_id": journal_id,
        "agent_name": agent_name,
        "repo_slug": repo_slug,
        "github_issue": github_issue,
    }
