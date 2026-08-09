"""Git worktree / PR helpers — split from skill_coding_agent."""
from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

from services.coding_pipeline import (
    detect_stack,
    get_coding_config,
    resolve_default_branch,
    resolve_pr_base_branch,
)
from services.dev_ownership import resolve_coding_agent
from skills.coding_agent_cli import run_command

logger = logging.getLogger(__name__)


def _resolve_spec_agent_id(spec: dict) -> str:
    """Resolve the real owning agent for this spec — never a hardcoded dev_app default."""
    paths = list(dict.fromkeys(
        (spec.get("files_to_create") or []) + (spec.get("files_to_modify") or [])
    ))
    return resolve_coding_agent(
        paths=paths,
        title=str(spec.get("title") or ""),
        description=str(spec.get("description") or ""),
        agent_id=str(spec.get("agent_id") or "").strip() or None,
    )

def _enforce_worktree_limit(repo_path: str, max_worktrees: int) -> None:
    """Prune stale worktrees, then refuse to create a new one past the configured cap."""
    if max_worktrees <= 0:
        return
    run_command(["git", "worktree", "prune"], cwd=repo_path)
    worktrees_dir = Path(repo_path) / "worktrees"
    if not worktrees_dir.is_dir():
        return
    active = [p for p in worktrees_dir.iterdir() if p.is_dir()]
    if len(active) >= max_worktrees:
        raise RuntimeError(
            f"Limite de worktrees atteinte ({len(active)}/{max_worktrees}) — "
            "réessaie une fois qu'un run en cours se termine."
        )

def _cleanup_stale_worktree(repo_path: str, branch: str, worktree_path: Path) -> None:
    """Remove leftover worktree/branch from a prior failed run (allows retry)."""
    if worktree_path.exists():
        run_command(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=repo_path,
        )
        if worktree_path.exists():
            shutil.rmtree(worktree_path, ignore_errors=True)
    run_command(["git", "worktree", "prune"], cwd=repo_path)
    _, listed, _ = run_command(["git", "branch", "--list", branch], cwd=repo_path)
    if branch in (listed or ""):
        run_command(["git", "branch", "-D", branch], cwd=repo_path)

def _prepare_worktree(spec: dict, branch: str) -> tuple[Path, str, dict]:
    """Create isolated worktree and return (path, default_branch, partial result)."""
    config = get_coding_config()
    repo_path = spec.get("repo_path")
    agent_id = _resolve_spec_agent_id(spec)
    _enforce_worktree_limit(repo_path, config.max_worktrees)
    worktree_path = Path(repo_path) / "worktrees" / f"{agent_id}-{branch.replace('/', '-')}"
    default_branch = resolve_default_branch(repo_path)
    result: dict = {
        "success": False,
        "pr_url": None,
        "branch": branch,
        "commit_sha": None,
        "claude_output": "",
        "stack": detect_stack(spec).value,
        "backend": config.backend,
        "error": None,
    }
    logger.info("[CodingAgent] Création worktree : %s", worktree_path)
    worktree_path.parent.mkdir(parents=True, exist_ok=True)
    _cleanup_stale_worktree(repo_path, branch, worktree_path)
    code, _out, err = run_command(
        ["git", "worktree", "add", str(worktree_path), "-b", branch, default_branch],
        cwd=repo_path,
    )
    if code != 0:
        raise RuntimeError(f"Échec création worktree : {err}")
    env_src = Path(repo_path) / ".env"
    env_dst = worktree_path / ".env"
    if env_src.is_file() and not env_dst.exists():
        shutil.copy2(env_src, env_dst)
    return worktree_path, default_branch, result

def _enforce_pre_pr_qa(worktree_path: Path, default_branch: str, spec: dict) -> dict:
    """Run QA gate; raises if checks fail."""
    # Agents sometimes create placeholder filenames from issue templates.
    for junk in worktree_path.glob("(aucun)"):
        junk.unlink(missing_ok=True)
    from services.coding_qa import run_pre_pr_qa
    qa = run_pre_pr_qa(str(worktree_path), spec, default_branch)
    if not qa["passed"]:
        detail = "\n".join(qa.get("errors") or [qa.get("summary", "QA failed")])
        raise RuntimeError(f"QA pre-PR échouée ({qa.get('stack')}): {detail[:800]}")
    return qa

def _finalize_pr(
    spec: dict,
    repo_path: str,
    worktree_path: Path,
    branch: str,
    result: dict,
) -> dict:
    """Push branch, open PR, set success fields."""
    config = get_coding_config()
    _, sha, _ = run_command(["git", "rev-parse", "HEAD"], cwd=str(worktree_path))
    result["commit_sha"] = sha.strip()
    code, _, push_err = run_command(
        ["git", "push", "-u", "origin", branch],
        cwd=str(worktree_path),
    )
    if code != 0:
        raise RuntimeError(f"Échec push : {push_err}")
    pr_title = spec.get("pr_title", f"[Auto] {spec['title']}")
    pr_body = spec.get(
        "pr_body",
        f"Tâche automatique générée par Dev App Agent.\n\nTask ID : `{spec['task_id']}`\n\n"
        f"Lancée le : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
    )
    pr_cmd = [
        "gh",
        "pr",
        "create",
        "--title",
        pr_title,
        "--body",
        pr_body,
        "--head",
        branch,
    ]
    pr_base = resolve_pr_base_branch(repo_path, config)
    if pr_base:
        pr_cmd.extend(["--base", pr_base])
    code, pr_out, pr_err = run_command(pr_cmd, cwd=repo_path)
    if code != 0:
        # Optional label — academy repo may not define it
        pr_cmd_label = pr_cmd + ["--label", "auto-generated"]
        code, pr_out, pr_err = run_command(pr_cmd_label, cwd=repo_path)
    if code != 0:
        raise RuntimeError(f"Échec création PR : {pr_err}")
    pr_url = pr_out.strip().split("\n")[-1]
    result["pr_url"] = pr_url
    result["success"] = True
    logger.info("[CodingAgent] [OK] PR créée : %s", pr_url)
    return result

def _worktree_has_changes(worktree_path: Path, default_branch: str) -> bool:
    """True if branch has file changes vs default branch."""
    _, diff_out, _ = run_command(
        ["git", "diff", default_branch, "--name-only"],
        cwd=str(worktree_path),
    )
    if diff_out.strip():
        return True
    _, status, _ = run_command(["git", "status", "--porcelain"], cwd=str(worktree_path))
    return bool(status.strip())

