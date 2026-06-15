"""
services/orchestration.py — Chaînes agent→agent pour n8n et l'orchestration autonome.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from agents.base import log_agent_action
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)

MORNING_COO_PROMPT = """Briefing du jour — agis en COO d'ALNUA.

1. Lis le briefing quotidien (get_daily_briefing si besoin).
2. Identifie les 3 priorités du jour (tickets ouverts, deadlines, alertes).
3. Pour chaque priorité : nomme l'agent responsable et l'action concrète.
4. Signale tout blocage nécessitant Emilie.

Format : plan d'action en 5 lignes max, pas de blabla."""

WEEKLY_COO_PROMPT = """Plan de la semaine — lundi matin, agis en COO d'ALNUA.

1. Synthèse des priorités de la semaine (projets Naïa / Wyrdheim / Eve / Hub).
2. Répartition des tâches par agent (pm, spec, qa, dev_app, dev_backend, marketing, content).
3. Deadlines et dépendances critiques.
4. Une recommandation pour protéger le temps d'Emilie.

Format : 8 lignes max, structuré par jour ou par projet."""


def _log_run(workflow: str, summary: str, *, success: bool = True) -> None:
    try:
        log_agent_action(
            get_supabase(),
            "coo",
            f"orchestration_{workflow}",
            input_summary=workflow,
            output_summary=summary[:200],
            status="success" if success else "error",
        )
    except Exception:
        pass


def _notify(message: str) -> dict[str, Any]:
    try:
        from skills.skill_hub_notify import notify_hub

        return notify_hub(message)
    except Exception:
        logger.exception("orchestration notify failed")
        return {"telegram": False, "discord": False}


def _resolve_project_id(
    project_id: str | None = None,
    project_slug: str | None = None,
) -> str | None:
    if project_id:
        return project_id
    db = get_supabase()
    try:
        if project_slug:
            rows = db.select("projects", filters={"slug": project_slug}, limit=1)
            if rows:
                return rows[0]["id"]
        for name in ("ALNUA", "ALNUA Hub"):
            rows = db.select("projects", filters={"name": name}, limit=1)
            if rows:
                return rows[0]["id"]
        rows = db.select("projects", limit=1)
        if rows:
            return rows[0]["id"]
    except Exception:
        pass
    return None


def run_morning_orchestration(*, weekly_plan: bool = False) -> dict[str, Any]:
    """Briefing quotidien enrichi (trends, coûts, events) + notification Telegram/Discord."""
    from services.daily_briefing import run_daily_briefing

    context = "Plan de la semaine — lundi matin." if weekly_plan else ""
    briefing_result: dict[str, Any] | None = None
    briefing_error: str | None = None
    try:
        briefing_result = run_daily_briefing(
            context=context,
            include_trends=True,
            include_costs=True,
            include_events=True,
        )
    except Exception as exc:
        briefing_error = str(exc)
        logger.exception("Morning orchestration: daily briefing failed")

    coo_brief = (briefing_result or {}).get("coo_brief") or {}
    coo_plan: str | None = None
    if coo_brief:
        coo_plan = "\n".join(
            line
            for line in (
                coo_brief.get("headline", ""),
                f"1. {coo_brief.get('priority_1', '')}",
                f"2. {coo_brief.get('priority_2', '')}",
                f"3. {coo_brief.get('priority_3', '')}",
            )
            if line and line.strip("123. ")
        ) or None

    briefing_row: dict[str, Any] | None = None
    if briefing_result:
        alerts = coo_brief.get("alerts") or []
        briefing_row = {
            "date": briefing_result.get("date"),
            "summary": coo_brief.get("headline", ""),
            "raw_data": briefing_result.get("raw_data"),
            "has_urgent": bool(alerts),
            "urgent_count": len(alerts),
            "pending_count": 0,
        }
        try:
            from services.briefing_generator import store_daily_briefing

            store_daily_briefing(get_supabase(), briefing_row)
        except Exception:
            logger.debug("Morning orchestration: Supabase briefing store skipped")

    success = briefing_result is not None and coo_plan is not None
    summary = (coo_plan or briefing_error or "partial")[:200]
    _log_run("morning", summary, success=success)

    notifications = {"telegram": False, "discord": False}
    if coo_plan:
        alerts = coo_brief.get("alerts") or []
        alert_block = ""
        if alerts:
            alert_block = "\n\n⚠️ Alertes :\n" + "\n".join(f"• {a}" for a in alerts[:5])
        opportunities = coo_brief.get("opportunities") or []
        opp_block = ""
        if opportunities:
            opp_block = "\n\n💡 Opportunités :\n" + "\n".join(f"• {o}" for o in opportunities[:3])
        mode = "Plan de la semaine" if weekly_plan else "Briefing du jour"
        academy_line = ""
        try:
            from services.academy_progress import get_academy_status

            ac = get_academy_status().get("progress") or {}
            academy_line = (
                f"\n\n🎓 Academy : {ac.get('completed_exercises', 0)}/"
                f"{ac.get('total_exercises', 52)} exos "
                f"(L{ac.get('current_level', 1)}, "
                f"{ac.get('success_rate_pct', 0)}% succès)"
            )
        except Exception:
            pass
        message = f"☀️ ALNUA — {mode}\n\n{coo_plan}{alert_block}{opp_block}{academy_line}"
        notifications = _notify(message)

    return {
        "workflow": "morning",
        "date": date.today().isoformat(),
        "weekly_plan": weekly_plan,
        "success": success,
        "briefing": briefing_row,
        "briefing_result": briefing_result,
        "briefing_error": briefing_error,
        "coo_plan": coo_plan,
        "coo_error": briefing_error if not coo_plan else None,
        "notifications": notifications,
    }


def run_spec_qa_chain(
    spec_text: str,
    *,
    context: str = "",
    rounds: int = 2,
    stop_on_approve: bool = True,
    create_qa_ticket: bool = True,
    project_id: str | None = None,
    project_slug: str | None = None,
    ticket_title: str | None = None,
) -> dict[str, Any]:
    """Léon ↔ Alex puis ticket QA optionnel + notification."""
    from agents.qa_agent import QAAgent
    from services.adversarial_spec import debate_spec

    try:
        result = debate_spec(spec_text, context, rounds, stop_on_approve)
        qa_ticket: dict[str, Any] | None = None
        ticket_error: str | None = None

        if create_qa_ticket:
            resolved_pid = _resolve_project_id(project_id, project_slug)
            if resolved_pid:
                try:
                    verdict = result.get("final_verdict", "revise")
                    priority = "high" if verdict == "reject" else "medium"
                    title = ticket_title or f"[Spec validée] {(context or spec_text)[:72]}"
                    divergences = result.get("divergences") or []
                    div_block = ""
                    if divergences:
                        div_block = "\n\n## Divergences restantes\n" + "\n".join(
                            f"- {d.get('critique', d)}" for d in divergences[:5]
                        )
                    description = (
                        f"## Spec convergée (Léon + Alex)\n\n"
                        f"{result.get('consensus_spec', spec_text)}\n\n"
                        f"**Verdict QA :** {verdict}\n"
                        f"**Contexte :** {context or '(non fourni)'}"
                        f"{div_block}"
                    )
                    qa_ticket = QAAgent().create_ticket_from_report(
                        project_id=resolved_pid,
                        title=title,
                        description=description,
                        ticket_type="improvement",
                        priority=priority,
                    )
                except Exception as exc:
                    ticket_error = str(exc)
                    logger.exception("spec_qa_chain: ticket creation failed")
            else:
                ticket_error = "project_id introuvable"

        _log_run(
            "spec_qa_chain",
            result.get("consensus_spec", "")[:200],
            success=True,
        )

        verdict = result.get("final_verdict", "?")
        msg = (
            f"📋 Spec QA — verdict **{verdict}**\n"
            f"{(context or ticket_title or 'Spec')[:120]}\n"
        )
        if qa_ticket:
            msg += f"\n✅ Ticket créé : {qa_ticket.get('title', '')[:80]}"
        elif ticket_error:
            msg += f"\n⚠️ Ticket non créé : {ticket_error}"
        notifications = _notify(msg)

        return {
            "workflow": "spec_qa_chain",
            "success": True,
            "qa_ticket": qa_ticket,
            "ticket_error": ticket_error,
            "notifications": notifications,
            **result,
        }
    except Exception as exc:
        logger.exception("spec_qa_chain failed")
        _log_run("spec_qa_chain", str(exc), success=False)
        _notify(f"❌ Spec QA échouée : {exc}")
        return {
            "workflow": "spec_qa_chain",
            "success": False,
            "error": str(exc),
        }


def run_github_pr_review(
    *,
    repo: str,
    pr_number: int,
    title: str = "",
    diff_summary: str = "",
    changed_files: str = "",
) -> dict[str, Any]:
    """Revue backend Hao Chen sur un PR GitHub."""
    from agents.dev_backend_agent import DevBackendAgent

    context = (
        f"Pull Request #{pr_number} sur {repo}\n"
        f"Titre : {title or '(sans titre)'}\n"
        f"Fichiers modifiés :\n{changed_files or '(non fourni)'}\n"
        f"Résumé des changements :\n{diff_summary or '(non fourni)'}"
    )
    code_block = diff_summary or changed_files or title

    try:
        review = DevBackendAgent().review_code(code_block[:8000], context)
        score = review.get("score", "?")
        _log_run("github_pr_review", f"PR #{pr_number} score={score}", success=True)
        issues = review.get("issues") or []
        critical = sum(1 for i in issues if i.get("severity") == "critical")
        msg = (
            f"🔍 Revue PR #{pr_number} — {repo}\n"
            f"Score : {score}/10 — {critical} critique(s)\n"
            f"{title[:100]}"
        )
        notifications = _notify(msg)
        return {
            "workflow": "github_pr_review",
            "success": True,
            "repo": repo,
            "pr_number": pr_number,
            "review": review,
            "notifications": notifications,
        }
    except Exception as exc:
        logger.exception("github_pr_review failed for PR #%s", pr_number)
        _log_run("github_pr_review", str(exc), success=False)
        _notify(f"❌ Revue PR #{pr_number} échouée : {exc}")
        return {
            "workflow": "github_pr_review",
            "success": False,
            "repo": repo,
            "pr_number": pr_number,
            "error": str(exc),
        }


def run_welcome_sequence(
    *,
    recipient_name: str,
    recipient_email: str,
    project: str = "ALNUA",
    language: str = "fr",
) -> dict[str, Any]:
    """Email de bienvenue via Nadia."""
    from agents.secretary_agent import SecretaryAgent

    subject = f"Bienvenue sur {project}"
    context = (
        f"Nouvel utilisateur : {recipient_name} ({recipient_email}). "
        f"Premier contact — email de bienvenue chaleureux et professionnel. "
        f"Projet : {project}."
    )

    try:
        draft = SecretaryAgent().draft_email(
            subject=subject,
            context=context,
            recipient=recipient_email,
            tone="chaleureux et professionnel",
            language=language,
        )
        _log_run("welcome_user", f"draft for {recipient_email}", success=True)
        notifications = _notify(
            f"👋 Bienvenue préparée — {recipient_name} ({recipient_email}) — {project}"
        )
        return {
            "workflow": "welcome_user",
            "success": True,
            "recipient_email": recipient_email,
            "draft": draft,
            "notifications": notifications,
        }
    except Exception as exc:
        logger.exception("welcome_sequence failed for %s", recipient_email)
        _log_run("welcome_user", str(exc), success=False)
        return {
            "workflow": "welcome_user",
            "success": False,
            "recipient_email": recipient_email,
            "error": str(exc),
        }


def run_content_sprint(
    *,
    brief: str,
    platforms: list[str] | None = None,
    project: str = "ALNUA",
) -> dict[str, Any]:
    """Sprint contenu multi-plateforme."""
    from services.content_pipeline import ContentBrief, run_pipeline

    if not platforms:
        platforms = ["linkedin", "discord", "twitter"]

    try:
        result = run_pipeline(
            ContentBrief(topic=brief, product=project, target_audience="communauté ALNUA"),
            platforms,
        )
        _log_run("content_sprint", brief[:100], success=True)
        posts = result.get("posts") or result.get("outputs") or []
        count = len(posts) if isinstance(posts, list) else 0
        notifications = _notify(
            f"📣 Sprint contenu — {count} format(s) généré(s)\n{brief[:200]}"
        )
        return {
            "workflow": "content_sprint",
            "success": True,
            "platforms": platforms,
            "notifications": notifications,
            **result,
        }
    except Exception as exc:
        logger.exception("content_sprint failed")
        _log_run("content_sprint", str(exc), success=False)
        _notify(f"❌ Sprint contenu échoué : {exc}")
        return {
            "workflow": "content_sprint",
            "success": False,
            "error": str(exc),
        }


def run_academy_sprint_orchestration(
    *,
    level: int | None = None,
    seed_if_missing: bool = True,
    mark_ready_count: int = 3,
) -> dict[str, Any]:
    """Seed + agent-ready pour l'académie ALNUA."""
    from services.academy_seed import run_academy_sprint

    try:
        result = run_academy_sprint(
            level=level,
            seed_if_missing=seed_if_missing,
            mark_ready_count=mark_ready_count,
        )
        marked = result.get("agent_ready", {}).get("marked_count", 0)
        _log_run("academy_sprint", f"level={level} ready={marked}")
        _notify(
            f"🎓 Sprint Académie ALNUA\n"
            f"Niveau : {level or 'auto'}\n"
            f"Issues agent-ready : {marked}"
        )
        return {**result, "success": True}
    except Exception as exc:
        logger.exception("academy_sprint failed")
        _log_run("academy_sprint", str(exc), success=False)
        _notify(f"❌ Sprint Académie échoué : {exc}")
        return {"workflow": "academy_sprint", "success": False, "error": str(exc)}


def run_academy_poll_orchestration(
    *,
    mark_ready_if_idle: bool = True,
    mark_ready_count: int = 2,
    notify: bool = True,
) -> dict[str, Any]:
    """
    Poll Academy infra: sync progress, close agent-done issues, advance level, queue next.
    Called by Hub poll_issues_loop backup + n8n workflow 12 every 30min.
    """
    from services.academy_issue_sync import run_academy_sync
    from services.academy_seed import mark_next_agent_ready
    from services.nuaway_gate import evaluate_nuaway_gate

    try:
        sync = run_academy_sync()
        progress = sync.get("progress") or {}
        levels = progress.get("levels") or {}
        lv1 = levels.get("1") or {}
        in_pipeline = int(lv1.get("in_progress") or 0)

        queued: dict[str, Any] | None = None
        if mark_ready_if_idle and in_pipeline == 0:
            current = int(progress.get("current_level") or 1)
            queued = mark_next_agent_ready(level=current, count=mark_ready_count)

        gate = evaluate_nuaway_gate(refresh_academy=False)

        summary = (
            f"L{progress.get('current_level')} "
            f"{progress.get('completed_exercises')}/{progress.get('total_exercises')} "
            f"gate={gate.get('readiness_pct')}%"
        )
        _log_run("academy_poll", summary)

        if notify:
            closed = sync.get("closed_issues", {}).get("closed_count", 0)
            ready_n = (queued or {}).get("marked_count", 0)
            msg = (
                f"🎓 Academy poll\n"
                f"Progression : {progress.get('completed_exercises')}/"
                f"{progress.get('total_exercises')} "
                f"(L{progress.get('current_level')})\n"
                f"Issues fermées : {closed} | agent-ready : {ready_n}\n"
                f"Gate readiness : {gate.get('readiness_pct')}%"
            )
            if gate.get("gate_open"):
                msg += "\n✅ GATE OUVERTE — Lounge/arcade autorisé"
            _notify(msg)

        return {
            "workflow": "academy_poll",
            "success": True,
            "sync": sync,
            "queued": queued,
            "gate": gate,
        }
    except Exception as exc:
        logger.exception("academy_poll failed")
        _log_run("academy_poll", str(exc), success=False)
        if notify:
            _notify(f"❌ Academy poll échoué : {exc}")
        return {"workflow": "academy_poll", "success": False, "error": str(exc)}


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


def run_nuaway_gate_orchestration(*, notify: bool = True) -> dict[str, Any]:
    """Évalue la gate NUAWAY et notifie si bloquante (n8n workflow 10)."""
    from services.nuaway_gate import evaluate_nuaway_gate

    try:
        result = evaluate_nuaway_gate(refresh_academy=True)
        pct = result.get("readiness_pct", 0)
        open_ = bool(result.get("gate_open"))
        _log_run("nuaway_gate", f"readiness={pct}% open={open_}")
        if notify:
            status = "✅ OPEN" if open_ else f"🔒 {pct}%"
            missing = [
                c["label"]
                for c in result.get("criteria", [])
                if c.get("critical") and not c.get("passed")
            ]
            msg = f"🚦 Gate NUAWAY — {status}"
            if missing and not open_:
                msg += f"\nBloquant : {missing[0]}"
            _notify(msg)
        return {**result, "success": True, "workflow": "nuaway_gate"}
    except Exception as exc:
        logger.exception("nuaway_gate failed")
        _log_run("nuaway_gate", str(exc), success=False)
        if notify:
            _notify(f"❌ Évaluation gate NUAWAY échouée : {exc}")
        return {"workflow": "nuaway_gate", "success": False, "error": str(exc)}


def run_nuaway_readiness_report_orchestration(*, notify: bool = True) -> dict[str, Any]:
    """Rapport readiness beta NUAWAY (n8n workflow 11)."""
    from services.nuaway_readiness import generate_readiness_report

    try:
        report = generate_readiness_report(refresh_gate=True)
        headline = report.get("headline", "")
        _log_run("nuaway_readiness_report", headline[:120])
        if notify:
            status = "✅ BETA READY" if report.get("beta_ready") else f"🔒 {report.get('readiness_pct')}%"
            _notify(f"📊 Rapport readiness NUAWAY\n{status}\n{headline}")
        return {**report, "success": True, "workflow": "nuaway_readiness_report"}
    except Exception as exc:
        logger.exception("nuaway_readiness_report failed")
        _log_run("nuaway_readiness_report", str(exc), success=False)
        if notify:
            _notify(f"❌ Rapport readiness échoué : {exc}")
        return {"workflow": "nuaway_readiness_report", "success": False, "error": str(exc)}


def run_nuaway_bootstrap_orchestration(*, notify: bool = True) -> dict[str, Any]:
    """Bootstrap ops NUAWAY — diagnostic + next steps (Phase 7)."""
    from services.nuaway_bootstrap import run_nuaway_bootstrap

    try:
        result = run_nuaway_bootstrap(refresh=True)
        headline = result.get("headline", "")
        _log_run("nuaway_bootstrap", headline[:120])
        if notify:
            steps = result.get("next_steps") or []
            step_txt = steps[0]["action"] if steps else "RAS"
            _notify(f"🚀 Bootstrap NUAWAY\n{headline}\n→ {step_txt}")
        return {**result, "success": True, "workflow": "nuaway_bootstrap"}
    except Exception as exc:
        logger.exception("nuaway_bootstrap failed")
        _log_run("nuaway_bootstrap", str(exc), success=False)
        if notify:
            _notify(f"❌ Bootstrap NUAWAY échoué : {exc}")
        return {"workflow": "nuaway_bootstrap", "success": False, "error": str(exc)}


WORKFLOW_CATALOG: list[dict[str, Any]] = [
    {
        "id": "morning",
        "name": "Briefing matinal + plan COO",
        "endpoint": "POST /orchestration/morning",
        "trigger": "Automatique lun-ven 08:00 + n8n",
        "agents": ["coo"],
        "level": 3,
    },
    {
        "id": "spec_qa_chain",
        "name": "Spec adversariale → ticket QA",
        "endpoint": "POST /orchestration/spec-qa-chain",
        "trigger": "Webhook n8n après spec",
        "agents": ["spec", "qa"],
        "level": 3,
    },
    {
        "id": "github_pr_review",
        "name": "Revue PR GitHub",
        "endpoint": "POST /orchestration/github-pr-review",
        "trigger": "Webhook n8n — GitHub PR",
        "agents": ["dev_backend"],
        "level": 4,
    },
    {
        "id": "welcome_user",
        "name": "Email de bienvenue",
        "endpoint": "POST /orchestration/welcome-user",
        "trigger": "Webhook n8n — nouvel inscrit",
        "agents": ["secretary"],
        "level": 4,
    },
    {
        "id": "content_sprint",
        "name": "Sprint contenu multi-plateforme",
        "endpoint": "POST /orchestration/content-sprint",
        "trigger": "Automatique vendredi 17:00 + n8n",
        "agents": ["content", "marketing"],
        "level": 2,
    },
    {
        "id": "academy_sprint",
        "name": "Sprint Académie dev_app",
        "endpoint": "POST /orchestration/academy-sprint",
        "trigger": "n8n workflow 08 — lundi 09:00",
        "agents": ["dev_app"],
        "level": 2,
    },
    {
        "id": "academy_poll",
        "name": "Poll Academy + sync + queue",
        "endpoint": "POST /orchestration/academy-poll",
        "trigger": "n8n workflow 12 — toutes les 30 min",
        "agents": ["dev_app"],
        "level": 2,
    },
    {
        "id": "prd_decompose",
        "name": "PRD Engineering → issues GitHub",
        "endpoint": "POST /orchestration/prd-decompose",
        "trigger": "n8n workflow 07 — après validation CEO",
        "agents": ["spec", "pm", "qa"],
        "level": 3,
    },
    {
        "id": "sentry_ingest",
        "name": "Sentry alert → hotfix issue",
        "endpoint": "POST /orchestration/sentry-ingest",
        "trigger": "n8n workflow 09 — alertes production",
        "agents": ["dev_app", "dev_backend", "qa"],
        "level": 4,
    },
    {
        "id": "nuaway_gate",
        "name": "Évaluation gate readiness NUAWAY",
        "endpoint": "POST /orchestration/nuaway-gate",
        "trigger": "n8n workflow 10 — check quotidien CEO",
        "agents": ["coo"],
        "level": 3,
    },
    {
        "id": "nuaway_readiness_report",
        "name": "Rapport readiness beta NUAWAY",
        "endpoint": "POST /orchestration/nuaway-readiness-report",
        "trigger": "n8n workflow 11 — rapport hebdo CEO",
        "agents": ["coo"],
        "level": 3,
    },
    {
        "id": "nuaway_bootstrap",
        "name": "Bootstrap ops NUAWAY",
        "endpoint": "POST /orchestration/nuaway-bootstrap",
        "trigger": "Manuel / post-setup — diagnostic + next steps",
        "agents": ["coo"],
        "level": 2,
    },
]
