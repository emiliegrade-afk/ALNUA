#!/usr/bin/env python3
"""
audit_autonomy_phase0.py — Phase 0 audit for ALNUA Autonomy Super Plan.

Usage:
    python scripts/audit_autonomy_phase0.py

Exit 0 if all blocking checks pass; 1 otherwise.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

PASS = "[OK]"
FAIL = "[FAIL]"
WARN = "[WARN]"
BLOCK = "[BLOCK]"


def _run(cmd: list[str], timeout: int = 30) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT),
        )
        out = (r.stdout or r.stderr or "").strip()
        return r.returncode == 0, out[:400]
    except FileNotFoundError:
        return False, "command not found"
    except subprocess.TimeoutExpired:
        return False, "timeout"


def check(name: str, ok: bool, detail: str = "", *, blocking: bool = True) -> bool:
    icon = PASS if ok else (BLOCK if blocking else WARN)
    suffix = f" — {detail}" if detail else ""
    print(f"{icon} {name}{suffix}")
    return ok or not blocking


def main() -> int:
    print("=" * 60)
    print("ALNUA Autonomy — Phase 0 Audit")
    print("=" * 60)

    blocking_failures = 0
    warnings = 0

    def record(ok: bool, blocking: bool = True) -> None:
        nonlocal blocking_failures, warnings
        if not ok:
            if blocking:
                blocking_failures += 1
            else:
                warnings += 1

    # --- Environment ---
    print("\n## Environment")
    for var in ("OPENROUTER_API_KEY", "SUPABASE_URL", "SUPABASE_KEY", "HUB_API_KEY"):
        ok = bool(os.getenv(var, "").strip())
        record(check(f"ENV {var}", ok, "manquant" if not ok else "défini"))

    gh_token = os.getenv("GITHUB_TOKEN", "").strip()
    record(check("ENV GITHUB_TOKEN", bool(gh_token)))

    # --- Pipeline config ---
    print("\n## Coding pipeline (Phase 1 settings)")
    try:
        from services.coding_pipeline import get_coding_config

        cfg = get_coding_config()
        record(
            check(
                "CodingPipelineConfig",
                cfg.timeout_s >= 600 and cfg.max_turns >= 10,
                f"timeout={cfg.timeout_s}s turns={cfg.max_turns} parallel={cfg.max_parallel} "
                f"auto_merge={cfg.auto_merge} base={cfg.merge_base_branch}",
            )
        )
    except Exception as exc:
        record(check("CodingPipelineConfig", False, str(exc)))

    # --- GitHub repos ---
    print("\n## GitHub repos")
    try:
        from config.github_repos import get_repo_targets, pipeline_enabled

        targets = get_repo_targets()
        record(check("pipeline_enabled()", pipeline_enabled(), f"{len(targets)} repo(s)"))
        for t in targets:
            path_ok = t.local_path.is_dir()
            must_exist = t.slug == "hub"
            record(
                check(
                    f"Local clone [{t.slug}]",
                    path_ok,
                    str(t.local_path) if path_ok else f"absent — {t.local_path}",
                    blocking=must_exist,
                )
            )
    except Exception as exc:
        record(check("github_repos", False, str(exc)))

    # --- CLI tools ---
    print("\n## CLI tools")
    ok, out = _run(["gh", "auth", "status"])
    record(check("gh CLI authenticated", ok, out.split("\n")[0] if out else ""))

    ok, out = _run(["claude", "--version"], timeout=15)
    record(
        check(
            "Claude Code CLI",
            ok,
            out or "installer : npm i -g @anthropic-ai/claude-code",
            blocking=False,
        )
    )

    ok, out = _run(["git", "--version"])
    record(check("git", ok, out))

    # --- Core modules ---
    print("\n## Core modules")
    modules = [
        "skills.skill_coding_agent",
        "skills.skill_gh_issues",
        "skills.skill_retry_loop",
        "skills.skill_error_journal",
        "skills.skill_agent_learning",
        "agents.bug_watchdog",
        "agents.fix_pipeline",
        "services.coding_pipeline",
        "services.academy_curriculum",
        "services.academy_progress",
        "services.academy_seed",
    ]
    for mod in modules:
        try:
            __import__(mod)
            record(check(f"import {mod}", True))
        except Exception as exc:
            record(check(f"import {mod}", False, str(exc)[:120]))

    # --- Stack detection smoke test ---
    print("\n## Stack detection")
    try:
        from services.coding_pipeline import DevStack, detect_stack

        expo = detect_stack(
            {
                "description": "Expo Router auth with Supabase",
                "files_to_create": ["app/login.tsx"],
                "repo_slug": "academy",
            }
        )
        record(check("detect_stack expo", expo == DevStack.REACT_NATIVE_EXPO, expo.value))

        api = detect_stack(
            {
                "description": "FastAPI endpoint",
                "files_to_create": ["api/health.py"],
                "repo_slug": "hub",
            }
        )
        record(check("detect_stack fastapi", api == DevStack.PYTHON_FASTAPI, api.value))
    except Exception as exc:
        record(check("detect_stack", False, str(exc)))

    # --- Mem0 (non-blocking) ---
    print("\n## Mem0")
    try:
        from skills.skill_mem0 import recall

        mem = recall(query="ALNUA dev_app test", agent_id="dev_app")
        check("Mem0 recall", True, "OK" if mem else "vide (seed optionnel)", blocking=False)
    except Exception as exc:
        check("Mem0 recall", False, str(exc)[:120], blocking=False)
        warnings += 1

    # --- Supabase error journal (non-blocking without live DB) ---
    print("\n## Supabase error journal")
    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        db.raw.table("agent_error_journal").select("id").limit(1).execute()
        check("agent_error_journal table", True, blocking=False)
    except Exception as exc:
        check(
            "agent_error_journal table",
            False,
            str(exc)[:120],
            blocking=False,
        )
        warnings += 1

    from services.academy_curriculum import all_exercises

    record(
        check(
            "Academy curriculum 52 exercises",
            len(all_exercises()) == 52,
            str(len(all_exercises())),
            blocking=False,
        )
    )

    # --- Files checklist ---
    print("\n## Files")
    files = [
        "docs/guides/PROMPT_VERIFICATION_AUDIT.md",
        ".github/ISSUE_TEMPLATE/agent_task.md",
        ".github/ISSUE_TEMPLATE/academy_exercise.md",
        "docs/guides/MCP_CURSOR_SETUP.md",
    ]
    for rel in files:
        p = ROOT / rel
        record(check(rel, p.is_file(), blocking=False))

    # --- Summary ---
    print("\n" + "=" * 60)
    if blocking_failures == 0:
        print(f"{PASS} Phase 0 : tous les contrôles bloquants passent ({warnings} avertissement(s))")
        print("\nProchaine étape : créer une issue agent-ready test ou lancer Phase 2 (Academy).")
        return 0
    print(f"{FAIL} Phase 0 : {blocking_failures} contrôle(s) bloquant(s), {warnings} avertissement(s)")
    print("\nActions suggérées :")
    if not gh_token:
        print("  - Renseigner GITHUB_TOKEN dans .env")
    if not shutil.which("claude"):
        print("  - Installer Claude Code CLI pour le coding autonome")
    print("  - Cloner les repos et configurer REPO_PATH_* / GITHUB_REPO_*")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
