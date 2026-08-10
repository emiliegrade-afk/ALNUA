"""Agent-to-agent chain workflows (spec, PR, welcome, content)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


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
    from services import orchestration as orch
    from services.adversarial_spec import debate_spec

    try:
        result = debate_spec(spec_text, context, rounds, stop_on_approve)
        qa_ticket: dict[str, Any] | None = None
        ticket_error: str | None = None

        if create_qa_ticket:
            resolved_pid = orch._resolve_project_id(project_id, project_slug)
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

        orch._log_run(
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
        notifications = orch._notify(msg)

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
        orch._log_run("spec_qa_chain", str(exc), success=False)
        orch._notify(f"❌ Spec QA échouée : {exc}")
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
    from services import orchestration as orch

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
        orch._log_run("github_pr_review", f"PR #{pr_number} score={score}", success=True)
        issues = review.get("issues") or []
        critical = sum(1 for i in issues if i.get("severity") == "critical")
        msg = (
            f"🔍 Revue PR #{pr_number} — {repo}\n"
            f"Score : {score}/10 — {critical} critique(s)\n"
            f"{title[:100]}"
        )
        notifications = orch._notify(msg)
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
        orch._log_run("github_pr_review", str(exc), success=False)
        orch._notify(f"❌ Revue PR #{pr_number} échouée : {exc}")
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
    from services import orchestration as orch

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
        orch._log_run("welcome_user", f"draft for {recipient_email}", success=True)
        notifications = orch._notify(
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
        orch._log_run("welcome_user", str(exc), success=False)
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
    from services import orchestration as orch
    from services.content_pipeline import ContentBrief, run_pipeline

    if not platforms:
        platforms = ["linkedin", "discord", "twitter"]

    try:
        result = run_pipeline(
            ContentBrief(topic=brief, product=project, target_audience="communauté ALNUA"),
            platforms,
        )
        orch._log_run("content_sprint", brief[:100], success=True)
        posts = result.get("posts") or result.get("outputs") or []
        count = len(posts) if isinstance(posts, list) else 0
        notifications = orch._notify(
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
        orch._log_run("content_sprint", str(exc), success=False)
        orch._notify(f"❌ Sprint contenu échoué : {exc}")
        return {
            "workflow": "content_sprint",
            "success": False,
            "error": str(exc),
        }
