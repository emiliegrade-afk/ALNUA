"""Sentry production alerts → error journal + GitHub hotfix issues (Phase 4)."""

from __future__ import annotations

from pathlib import Path

from skills.skill_error_journal import log_error

from services.sentry_ops_dedup import load_dedup as _load_dedup
from services.sentry_ops_github import create_hotfix_github_issue, format_hotfix_issue_body
from services.sentry_ops_ingest import ingest_sentry_event
from services.sentry_ops_parse import SentryIngestEvent, parse_sentry_webhook, verify_sentry_signature
from services.sentry_ops_resolve import resolve_agent_from_sentry, resolve_repo_slug_from_sentry

_DEDUP_PATH = Path(__file__).resolve().parent.parent / "data" / "sentry_ingest.json"

__all__ = [
    "SentryIngestEvent",
    "_DEDUP_PATH",
    "_load_dedup",
    "create_hotfix_github_issue",
    "format_hotfix_issue_body",
    "ingest_sentry_event",
    "log_error",
    "parse_sentry_webhook",
    "resolve_agent_from_sentry",
    "resolve_repo_slug_from_sentry",
    "verify_sentry_signature",
]
