"""Dev Integrator Agent — Rayan Kone, intégrateur ALNUA (merge worktrees, gate QA, PR)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from agents.agent_base import AgentBase
from agents.base import log_agent_action
from config.agent_operating_spec import get_system_prompt


class DevIntegratorAgent(AgentBase):
    AGENT_NAME = "dev_integrator"

    SYSTEM_PROMPT = get_system_prompt("dev_integrator")

    def integrate_worktrees(
        self,
        repo_path: str,
        branch: str,
        worktrees: list[str] | None = None,
        base_branch: str = "",
    ) -> dict[str, Any]:
        """Fusionne les branches des devs dans une branche d'intégration cloisonnée.

        `worktrees` = noms des branches Git des devs à intégrer (pas des chemins disque —
        elles partagent le même repo, un `git merge` suffit). Opère dans son propre worktree
        (worktrees/dev_integrator-{branch}/), jamais dans le repo actif. Ne pousse rien : le
        merge reste local tant que open_integration_pr n'a pas eu l'approbation QA.
        """
        from skills.skill_coding_agent import _cleanup_stale_worktree, run_command
        from services.coding_pipeline import get_coding_config, resolve_default_branch

        config = get_coding_config()
        default_branch = resolve_default_branch(repo_path)
        target_base = base_branch or config.merge_base_branch or default_branch
        branches_to_merge = [b for b in (worktrees or []) if b]

        if not branches_to_merge:
            return {
                "status": "noop", "branch": branch, "merged": [], "conflicts": [],
                "error": "Aucune branche à merger",
            }

        integrator_worktree = Path(repo_path) / "worktrees" / f"dev_integrator-{branch.replace('/', '-')}"
        integrator_worktree.parent.mkdir(parents=True, exist_ok=True)
        _cleanup_stale_worktree(repo_path, branch, integrator_worktree)

        run_command(["git", "fetch", "origin"], cwd=repo_path)
        code, _out, err = run_command(
            ["git", "worktree", "add", str(integrator_worktree), "-b", branch, target_base],
            cwd=repo_path,
        )
        if code != 0:
            return {
                "status": "error", "branch": branch, "merged": [], "conflicts": [],
                "error": f"Échec création worktree intégration : {err}",
            }

        merged: list[str] = []
        conflicts: list[dict[str, str]] = []
        for source_branch in branches_to_merge:
            run_command(["git", "fetch", "origin", source_branch], cwd=str(integrator_worktree))
            code, out, err = run_command(
                ["git", "merge", "--no-ff", "--no-edit", source_branch],
                cwd=str(integrator_worktree),
            )
            if code == 0:
                merged.append(source_branch)
                continue
            run_command(["git", "merge", "--abort"], cwd=str(integrator_worktree))
            conflicts.append({"branch": source_branch, "error": (err or out)[:500]})

        qa_verdict: dict[str, Any] = {"verdict": "skipped", "summary": "Aucun changement à review"}
        if merged:
            _, diff_text, _ = run_command(
                ["git", "diff", f"{target_base}...HEAD"],
                cwd=str(integrator_worktree),
            )
            qa_verdict = self.review_diff(
                diff_summary=diff_text,
                context=f"Intégration {branch} <- {', '.join(merged)}",
            )

        if merged and not conflicts and qa_verdict.get("verdict") == "approved":
            status = "integrated"
        elif merged and not conflicts:
            status = "merged_pending_qa"
        elif merged:
            status = "partial"
        else:
            status = "failed"

        log_agent_action(
            self.db, self.AGENT_NAME, "integrate_worktrees",
            input_summary=f"{branch} <- {branches_to_merge}",
            output_summary=f"status={status} qa={qa_verdict.get('verdict')}",
            status="success" if status != "failed" else "error",
        )
        return {
            "status": status,
            "branch": branch,
            "base_branch": target_base,
            "worktree": str(integrator_worktree),
            "merged": merged,
            "conflicts": conflicts,
            "qa_verdict": qa_verdict,
        }

    def open_integration_pr(
        self,
        repo_path: str,
        branch: str,
        title: str,
        body: str = "",
        qa_verdict: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Push + ouvre la PR d'intégration — REFUSE si la review QA n'est pas approuvée."""
        from skills.skill_coding_agent import run_command
        from services.coding_pipeline import get_coding_config, resolve_default_branch

        config = get_coding_config()
        worktree = Path(repo_path) / "worktrees" / f"dev_integrator-{branch.replace('/', '-')}"
        work_cwd = str(worktree) if worktree.is_dir() else repo_path
        base = config.merge_base_branch or resolve_default_branch(repo_path)

        verdict = qa_verdict
        if verdict is None:
            _, diff_text, _ = run_command(["git", "diff", f"{base}...HEAD"], cwd=work_cwd)
            if not diff_text.strip():
                return {"status": "noop", "branch": branch, "error": "Rien à intégrer (diff vide)"}
            verdict = self.review_diff(diff_summary=diff_text, context=f"PR intégration {branch}")

        if verdict.get("verdict") != "approved":
            log_agent_action(
                self.db, self.AGENT_NAME, "open_integration_pr",
                input_summary=branch,
                output_summary=f"BLOQUÉ par QA : {verdict.get('summary', '')}",
                status="error",
            )
            return {
                "status": "blocked_by_qa",
                "branch": branch,
                "qa_verdict": verdict,
                "error": "PR non ouverte : review QA non approuvée",
            }

        code, _, err = run_command(["git", "push", "-u", "origin", branch], cwd=work_cwd)
        if code != 0:
            return {"status": "error", "branch": branch, "error": f"Échec push : {err}"}

        pr_body = body or f"Intégration automatique — QA : {verdict.get('summary', 'approuvé')}."
        code, out, err = run_command(
            ["gh", "pr", "create", "--title", title, "--body", pr_body, "--base", base, "--head", branch],
            cwd=work_cwd,
        )
        if code != 0:
            return {"status": "error", "branch": branch, "error": f"Échec création PR : {err}"}

        pr_url = (out or "").strip().splitlines()[-1] if (out or "").strip() else ""
        log_agent_action(
            self.db, self.AGENT_NAME, "open_integration_pr",
            input_summary=branch,
            output_summary=f"PR ouverte : {pr_url}",
            status="success",
        )
        return {"status": "pr_ready", "branch": branch, "title": title, "pr_url": pr_url, "qa_verdict": verdict}

    def review_diff(self, diff_summary: str, context: str = "") -> dict[str, Any]:
        """Délègue systématiquement à QA (senior) — l'intégrateur ne s'auto-valide jamais."""
        from agents.qa_agent import QAAgent

        return QAAgent(db=self.db).review_diff(diff_summary=diff_summary, context=context)
