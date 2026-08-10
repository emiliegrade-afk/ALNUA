"""PRD decompose and production/security ingest orchestration."""

from __future__ import annotations

import logging
from typing import Any

from services.orchestration_helpers import _log_run, _notify

logger = logging.getLogger(__name__)


def run_prd_decompose_orchestration(
    *,
    dossier_id: str,
    repo_slug: str | None = None,
    dry_run: bool = False,
    mark_ready_count: int = 3,
    force_spec: bool = False,
) -> dict[str, Any]:
    """CEO approved → engineering spec → GitHub issues (n8n workflow 07)."""
    from services.prd_engineering import run_prd_decompose

    try:
        result = run_prd_decompose(
            dossier_id,
            repo_slug=repo_slug,
            dry_run=dry_run,
            mark_ready_count=mark_ready_count,
            force_spec=force_spec,
        )
        created = result.get("created_count", 0)
        _log_run("prd_decompose", f"dossier={dossier_id} issues={created}")
        _notify(
            f"📋 PRD → Issues GitHub\n"
            f"Dossier : {result.get('dossier_slug')}\n"
            f"Issues créées : {created}\n"
            f"Repo : {result.get('github_repo')}"
        )
        return {**result, "success": True, "workflow": "prd_decompose"}
    except Exception as exc:
        logger.exception("prd_decompose failed")
        _log_run("prd_decompose", str(exc), success=False)
        _notify(f"❌ PRD decompose échoué : {exc}")
        return {"workflow": "prd_decompose", "success": False, "error": str(exc)}


def run_sentry_ingest_orchestration(payload: dict[str, Any]) -> dict[str, Any]:
    """Replay Sentry payload via orchestration (n8n workflow 09)."""
    from services.production_ops import run_sentry_webhook

    try:
        # Caller already authenticated via X-Hub-Key on /orchestration/*.
        result = run_sentry_webhook(
            payload,
            create_issue=True,
            trusted_relay=True,
        )
        action = result.get("action", "unknown")
        _log_run("sentry_ingest", f"action={action}")
        if action == "ingested":
            _notify(
                f"🚨 Sentry → hotfix\n"
                f"{result.get('fingerprint', '')[:12]}…\n"
                f"Journal : {result.get('journal_id', '—')}\n"
                f"Issue : #{(result.get('github_issue') or {}).get('number', '—')}"
            )
        return {**result, "workflow": "sentry_ingest"}
    except Exception as exc:
        logger.exception("sentry_ingest failed")
        _log_run("sentry_ingest", str(exc), success=False)
        _notify(f"❌ Sentry ingest échoué : {exc}")
        return {"workflow": "sentry_ingest", "success": False, "error": str(exc)}


def run_security_ingest_orchestration(payload: dict[str, Any]) -> dict[str, Any]:
    """Security barrier events (RESONANCE fortress) → notify + journal."""
    from services.security_ops import run_security_ingest

    try:
        result = run_security_ingest(payload)
        _log_run("security_ingest", f"type={result.get('type')} sev={result.get('severity')}")
        return result
    except Exception as exc:
        logger.exception("security_ingest failed")
        _log_run("security_ingest", str(exc), success=False)
        _notify(f"❌ Security ingest échoué : {exc}")
        return {"workflow": "security_ingest", "success": False, "error": str(exc)}
