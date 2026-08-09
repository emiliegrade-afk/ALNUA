"""Workflow step handlers — run_ops, semaine, explore, sav_lite (BUG-004 split)."""

from __future__ import annotations

import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)

StepStatus = Literal["PENDING", "IN_PROGRESS", "OK", "A_VERIFIER", "ECART"]


def _step_scan_registry(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.app_registry import list_apps

    branch_filter = ctx.get("branch")
    apps = [a for a in list_apps(include_disabled=False) if a.slug != "hub"]
    if branch_filter:
        apps = [a for a in apps if a.branch == branch_filter]

    if not apps:
        return {"status": "ECART", "detail": "Aucune app active dans le registry", "gaps": ["registry.empty"]}

    return {
        "status": "OK",
        "detail": f"{len(apps)} app(s) surveillée(s)",
        "result": {
            "apps": [
                {
                    "slug": a.slug,
                    "name": a.name,
                    "branch": a.branch,
                    "path_exists": a.path_exists,
                    "lifecycle_status": getattr(a, "lifecycle_status", "build"),
                }
                for a in apps
            ]
        },
    }


def _step_scan_errors(ctx: dict[str, Any], prior_steps: list[Any]) -> dict[str, Any]:
    from services.company_errors import summarize_open_by_repo

    scan = next((s.result for s in prior_steps if s.step_id == "scan_registry"), None)
    apps = (scan or {}).get("apps") or []
    if not apps:
        return {"status": "ECART", "detail": "scan_registry requis", "gaps": ["scan_registry"]}

    per_repo = summarize_open_by_repo()
    total_open = sum(r["open_count"] for r in per_repo)

    status: StepStatus = "OK"
    if total_open > 10:
        status = "A_VERIFIER"
    detail = f"{total_open} erreur(s) ouverte(s) sur {len(apps)} repo(s)"
    if per_repo:
        detail += f" — actifs : {', '.join(r['slug'] for r in per_repo)}"

    return {
        "status": status,
        "detail": detail,
        "result": {"total_open": total_open, "repos_with_errors": per_repo},
        "gaps": [f"{r['slug']}:{r['open_count']}" for r in per_repo] if total_open > 10 else [],
    }


def _step_remediate_errors(ctx: dict[str, Any], prior_steps: list[Any]) -> dict[str, Any]:
    if not ctx.get("auto_remediate", True):
        return {"status": "OK", "detail": "Auto-remédiation désactivée", "result": {"skipped": True}}

    scan = next((s.result for s in prior_steps if s.step_id == "scan_errors"), None)
    total_open = (scan or {}).get("total_open") or 0
    if total_open < 1:
        return {"status": "OK", "detail": "Aucune erreur — rien à remédier", "result": {"count": 0}}

    from services.company_errors import auto_create_fix_issues

    outcome = auto_create_fix_issues(max_issues=int(ctx.get("max_auto_issues", 5)))
    created = outcome.get("created") or []
    if not created and outcome.get("error"):
        return {
            "status": "A_VERIFIER",
            "detail": outcome.get("error", "auto-issues échoué"),
            "result": outcome,
        }
    return {
        "status": "OK",
        "detail": f"{len(created)} issue(s) agent-ready créée(s)",
        "result": outcome,
    }


def _step_weekly_briefing(ctx: dict[str, Any]) -> dict[str, Any]:
    try:
        from services.daily_briefing import run_quick_briefing

        brief = run_quick_briefing()
        headline = brief.get("headline") or brief.get("summary") or "Brief généré"
        return {"status": "OK", "detail": str(headline)[:200], "result": brief}
    except Exception as exc:
        return {"status": "A_VERIFIER", "detail": str(exc)[:200], "gaps": ["briefing"]}


def _step_ops_snapshot(ctx: dict[str, Any], prior_steps: list[Any]) -> dict[str, Any]:
    from services.company_errors import summarize_open_by_repo
    from services.run_watchdog_registry import build_watchdog_coverage_report

    per_repo = summarize_open_by_repo()
    total = sum(r["open_count"] for r in per_repo)
    wd = build_watchdog_coverage_report()
    detail = f"{total} erreur(s) · {wd.get('summary', '')}"
    return {
        "status": "A_VERIFIER" if total > 5 else "OK",
        "detail": detail,
        "result": {"total_open": total, "repos": per_repo, "watchdog": wd},
    }


def _step_ceo_queue_reminder(ctx: dict[str, Any]) -> dict[str, Any]:
    try:
        from agents.rnd_ceo_agent import RndCeoAgent

        queue = RndCeoAgent().list_ceo_queue(limit=10)
        to_validate = queue.get("to_validate") or []
        to_prepare = queue.get("to_prepare") or []
        if not to_validate and not to_prepare:
            return {
                "status": "OK",
                "detail": "Aucun dossier en attente — ta validation produit n'est pas requise",
                "result": queue,
            }
        titles = [d.get("title", "?")[:40] for d in to_validate[:3]]
        detail = (
            f"{len(to_validate)} à valider, {len(to_prepare)} à préparer"
            + (f" — ex: {', '.join(titles)}" if titles else "")
        )
        return {
            "status": "A_VERIFIER",
            "detail": detail + " (decision CEO requise)",
            "result": queue,
            "gaps": ["ceo.validation_pending"],
        }
    except Exception as exc:
        return {"status": "A_VERIFIER", "detail": str(exc)[:200], "gaps": ["ceo_queue"]}


def _step_cost_snapshot(ctx: dict[str, Any]) -> dict[str, Any]:
    try:
        from services.cost_monitor import check_budget_alert, get_cost_report

        report = get_cost_report(days=7)
        alert = check_budget_alert(daily_budget_usd=float(ctx.get("daily_budget_usd", 10.0)))
        total = report.get("total_usd") or report.get("total_cost_usd") or 0
        severity = alert.get("severity", "ok")
        status: StepStatus = "OK" if severity == "ok" else "A_VERIFIER"
        return {
            "status": status,
            "detail": f"7j : ${total:.2f} USD · alerte {severity}",
            "result": {"report": report, "alert": alert},
        }
    except Exception as exc:
        return {"status": "A_VERIFIER", "detail": str(exc)[:120], "gaps": ["cost"]}


def _step_watchdog_status(ctx: dict[str, Any], prior_steps: list[Any]) -> dict[str, Any]:
    from services.run_watchdog_registry import build_watchdog_coverage_report

    report = build_watchdog_coverage_report()
    unmapped = report.get("unmapped_slugs") or []
    gaps = [f"watchdog.unmapped.{s}" for s in unmapped]

    status: StepStatus = "OK"
    if unmapped:
        status = "A_VERIFIER"

    return {
        "status": status,
        "detail": report.get("summary", ""),
        "result": report,
        "gaps": gaps,
    }


def _step_start_investigation(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.rnd_hypothesis_tree import start_investigation

    topic = (ctx.get("topic") or ctx.get("query") or "").strip()
    if not topic:
        return {"status": "ECART", "detail": "topic requis", "gaps": ["context.topic"]}

    result = start_investigation(topic, requested_by=ctx.get("requested_by", "workflow_engine"))
    if not result.get("success"):
        return {"status": "ECART", "detail": result.get("error", "échec"), "gaps": ["investigation"]}
    return {
        "status": "OK",
        "detail": f"Arbre lancé : {result.get('slug')}",
        "result": result,
    }


def _step_sync_product_kb(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.product_kb import sync_kb_from_registry

    outcome = sync_kb_from_registry(only_prod_beta=bool(ctx.get("only_prod_beta", False)))
    synced = outcome.get("synced", 0)
    if synced < 1:
        return {
            "status": "A_VERIFIER",
            "detail": "Aucun produit synchronisé dans product_kb",
            "gaps": ["product_kb.empty"],
            "result": outcome,
        }
    return {
        "status": "OK",
        "detail": f"{synced} fiche(s) KB synchronisée(s)",
        "result": outcome,
    }


def _step_ingest_beta_feedback(ctx: dict[str, Any]) -> dict[str, Any]:
    if ctx.get("skip_beta_ingest"):
        return {"status": "OK", "detail": "Ingest beta ignoré", "result": {"skipped": True}}

    from services.sav_lite import ingest_recent_beta_feedback

    outcome = ingest_recent_beta_feedback(
        days=int(ctx.get("beta_days", 7)),
        limit=int(ctx.get("beta_limit", 10)),
    )
    ingested = outcome.get("ingested", 0)
    if outcome.get("error"):
        return {
            "status": "A_VERIFIER",
            "detail": outcome.get("error", "ingest beta échoué"),
            "result": outcome,
            "gaps": ["beta_ingest"],
        }
    return {
        "status": "OK" if ingested >= 0 else "A_VERIFIER",
        "detail": f"{ingested} cas SAV créé(s) depuis le feedback beta",
        "result": outcome,
    }


def _step_sav_ceo_pending(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.sav_lite import list_sav_cases

    pending = list_sav_cases(status="awaiting_ceo", needs_ceo=True, limit=20)
    draft_ready = list_sav_cases(status="draft_ready", limit=20)

    if not pending and not draft_ready:
        return {
            "status": "OK",
            "detail": "Aucun cas SAV en attente",
            "result": {"awaiting_ceo": 0, "draft_ready": 0},
        }

    subjects = [c.get("subject", "?")[:40] for c in pending[:3]]
    detail = f"{len(pending)} validation CEO · {len(draft_ready)} brouillon(s) prêt(s)"
    if subjects:
        detail += f" — ex: {', '.join(subjects)}"

    status: StepStatus = "A_VERIFIER" if pending else "OK"
    gaps = ["sav.ceo_validation"] if pending else []

    if pending and ctx.get("notify_ceo", True):
        try:
            from skills.skill_telegram_notify import notify_telegram

            notify_telegram(
                f"📋 SAV — {len(pending)} cas à valider sur /secretary\n"
                + "\n".join(f"• {s}" for s in subjects[:5])
            )
        except Exception:
            pass

    return {
        "status": status,
        "detail": detail,
        "result": {"awaiting_ceo": len(pending), "draft_ready": len(draft_ready), "pending": pending[:5]},
        "gaps": gaps,
    }
