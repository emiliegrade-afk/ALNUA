"""Autonomous coding pipeline configuration and helpers (Super Plan Phases 0–1)."""

from __future__ import annotations

import logging
import os
import re
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from functools import lru_cache

logger = logging.getLogger(__name__)


class DevStack(StrEnum):
    PYTHON_FASTAPI = "python_fastapi"
    REACT_NATIVE_EXPO = "react_native_expo"
    NEXTJS = "nextjs"
    TYPESCRIPT = "typescript"


@dataclass(frozen=True)
class CodingPipelineConfig:
    timeout_s: int
    max_turns: int
    max_parallel: int
    auto_merge: bool
    academy_auto_merge: bool
    merge_base_branch: str
    max_worktrees: int
    backend: str
    aider_model: str
    qa_required: bool


@lru_cache
def get_coding_config() -> CodingPipelineConfig:
    """Read pipeline tuning from env (via settings when available)."""
    try:
        from config.settings import get_settings

        s = get_settings()
        return CodingPipelineConfig(
            timeout_s=s.coding_timeout_s,
            max_turns=s.coding_max_turns,
            max_parallel=s.coding_max_parallel,
            auto_merge=s.coding_auto_merge,
            academy_auto_merge=s.coding_academy_auto_merge,
            merge_base_branch=s.coding_merge_base_branch.strip(),
            max_worktrees=s.coding_max_worktrees,
            backend=s.coding_backend.strip().lower() or "hub",
            aider_model=(s.aider_model or "").strip(),
            qa_required=s.coding_qa_required,
        )
    except Exception:
        return CodingPipelineConfig(
            timeout_s=int(os.getenv("CODING_TIMEOUT_S", "3600")),
            max_turns=int(os.getenv("CODING_MAX_TURNS", "60")),
            max_parallel=int(os.getenv("CODING_MAX_PARALLEL", "2")),
            auto_merge=os.getenv("CODING_AUTO_MERGE", "false").lower() in ("1", "true", "yes"),
            academy_auto_merge=os.getenv("CODING_ACADEMY_AUTO_MERGE", "true").lower()
            in ("1", "true", "yes"),
            merge_base_branch=os.getenv("CODING_MERGE_BASE_BRANCH", "staging").strip(),
            max_worktrees=int(os.getenv("CODING_MAX_WORKTREES", "8")),
            backend=os.getenv("CODING_BACKEND", "hub").strip().lower(),
            aider_model=os.getenv("AIDER_MODEL", "").strip(),
            qa_required=os.getenv("CODING_QA_REQUIRED", "true").lower() in ("1", "true", "yes"),
        )


_STACK_HINTS: dict[DevStack, tuple[str, ...]] = {
    DevStack.REACT_NATIVE_EXPO: (
        "expo",
        "react-native",
        "react native",
        "app.tsx",
        "app.json",
        "eas.json",
        "detox",
        "securestore",
        "mapbox",
    ),
    DevStack.NEXTJS: (
        "next.js",
        "nextjs",
        "next.config",
        "app/page.tsx",
        "app router",
        "shadcn",
    ),
    DevStack.PYTHON_FASTAPI: (
        "fastapi",
        "pydantic",
        "api/main.py",
        "uvicorn",
        "pytest",
        "api/schemas",
    ),
    DevStack.TYPESCRIPT: ("typescript", "package.json"),
}

_REPO_DEFAULT_STACK: dict[str, DevStack] = {
    "academy": DevStack.REACT_NATIVE_EXPO,
    "hub": DevStack.PYTHON_FASTAPI,
}


def detect_stack(spec: dict) -> DevStack:
    """Infer target stack from issue spec (files, description, repo slug)."""
    explicit = (spec.get("stack") or "").strip().lower()
    if explicit:
        for stack in DevStack:
            if stack.value == explicit or explicit in stack.value:
                return stack
        if explicit in ("rn", "expo", "react-native"):
            return DevStack.REACT_NATIVE_EXPO
        if explicit in ("next", "nextjs"):
            return DevStack.NEXTJS
        if explicit in ("python", "fastapi", "api"):
            return DevStack.PYTHON_FASTAPI

    blob_parts = [
        spec.get("description") or "",
        spec.get("title") or "",
        " ".join(spec.get("files_to_create") or []),
        " ".join(spec.get("files_to_modify") or []),
        " ".join(spec.get("tests_to_pass") or []),
    ]
    blob = " ".join(blob_parts).lower()

    scores: dict[DevStack, int] = {s: 0 for s in DevStack}
    for stack, hints in _STACK_HINTS.items():
        for hint in hints:
            if hint in blob:
                scores[stack] += 1

    # File extensions: .tsx before .ts (avoid false positive)
    file_blob = " ".join(
        (spec.get("files_to_create") or [])
        + (spec.get("files_to_modify") or [])
    ).lower()
    if file_blob.endswith(".tsx") or ".tsx" in file_blob:
        scores[DevStack.REACT_NATIVE_EXPO] += 2
        scores[DevStack.NEXTJS] += 1
    elif file_blob.endswith(".ts") or ".ts" in file_blob:
        scores[DevStack.TYPESCRIPT] += 1

    best_score = max(scores.values())
    if best_score > 0:
        for stack in (
            DevStack.REACT_NATIVE_EXPO,
            DevStack.NEXTJS,
            DevStack.PYTHON_FASTAPI,
            DevStack.TYPESCRIPT,
        ):
            if scores[stack] == best_score:
                return stack

    slug = (spec.get("repo_slug") or spec.get("_repo_slug") or "").lower()
    return _REPO_DEFAULT_STACK.get(slug, DevStack.PYTHON_FASTAPI)


_STACK_PROMPTS: dict[DevStack, str] = {
    DevStack.PYTHON_FASTAPI: """STACK : Python 3.12 + FastAPI + Pydantic + Supabase.
- Logging via logger = logging.getLogger(__name__), jamais print()
- Variables d'env via os.getenv() + valeur par défaut
- Nouvelles deps → requirements.txt
- Tests : pytest dans tests/""",
    DevStack.REACT_NATIVE_EXPO: """STACK : React Native + Expo SDK 56 + TypeScript + Supabase JS.
- Pas de print() — utiliser console.warn en dev seulement si nécessaire
- Secrets dans .env / app.config — jamais hardcodés
- Navigation : Expo Router (app/ directory)
- Nouvelles deps Expo : versions ~56.x uniquement — jamais ~12.x (utiliser `npx expo install <pkg>`)
- Auth : @supabase/supabase-js ; session via supabase.auth
- Ne jamais créer de fichier vide ni de fichier hors arborescence app/lib/hooks/components
- Ne pas ajouter CLAUDE.md, AGENTS.md, .aider.* (réservés au Hub ALNUA, pas Academy)
- Tab bar : MaterialIcons (TabBarIcon) — jamais expo-symbols/SymbolView (crash web)
- Supprimer boilerplate Expo (EditScreenInfo, « Tab One ») — écran Accueil réel
- Géoloc : fallback coords par défaut si permission refusée (surtout web)
- UI : Pressable + StyleSheet — éviter Button RN brut sur web
- Tests : `npx tsc --noEmit` ET `npm test` doivent passer avant PR""",
    DevStack.NEXTJS: """STACK : Next.js 14+ App Router + TypeScript + Tailwind + shadcn/ui.
- Server Components par défaut ; 'use client' seulement si requis
- Appels API via web/src/lib/* — pas de fetch dans les composants UI
- Env : NEXT_PUBLIC_* pour le client, secrets côté serveur uniquement
- Tests : pytest backend OU playwright/jest selon le repo""",
    DevStack.TYPESCRIPT: """STACK : TypeScript strict (no any).
- Suivre la structure et les conventions du repo existant
- Tests selon le framework déjà configuré""",
}


def stack_expert_role(stack: DevStack) -> str:
    roles = {
        DevStack.PYTHON_FASTAPI: "expert Python/FastAPI backend",
        DevStack.REACT_NATIVE_EXPO: "expert React Native / Expo mobile",
        DevStack.NEXTJS: "expert Next.js App Router frontend",
        DevStack.TYPESCRIPT: "expert TypeScript fullstack",
    }
    return roles.get(stack, "expert développeur ALNUA")


def stack_rules_block(stack: DevStack) -> str:
    return _STACK_PROMPTS.get(stack, _STACK_PROMPTS[DevStack.PYTHON_FASTAPI])


def branch_exists(repo_path: str, branch: str) -> bool:
    if not branch:
        return False
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/heads/{branch}"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            return True
        result = subprocess.run(
            ["git", "ls-remote", "--heads", "origin", branch],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return bool(result.stdout.strip())
    except Exception as exc:
        logger.debug("branch_exists(%s): %s", branch, exc)
        return False


def resolve_pr_base_branch(repo_path: str, config: CodingPipelineConfig | None = None) -> str | None:
    """PR target branch when auto-merge is enabled (staging preferred)."""
    cfg = config or get_coding_config()
    if not cfg.auto_merge:
        return None
    candidate = cfg.merge_base_branch
    if candidate and branch_exists(repo_path, candidate):
        return candidate
    logger.warning(
        "[CodingPipeline] Auto-merge activé mais branche '%s' absente sur %s",
        candidate,
        repo_path,
    )
    return None


def should_auto_merge_repo(repo_slug: str | None, config: CodingPipelineConfig | None = None) -> bool:
    """True when PRs for this repo should merge automatically after QA."""
    cfg = config or get_coding_config()
    if cfg.auto_merge:
        return True
    if (repo_slug or "").lower() == "academy" and cfg.academy_auto_merge:
        return True
    return False


def merge_pr_if_allowed(
    repo_path: str,
    pr_number: int,
    *,
    tests_passed: bool,
    repo_slug: str | None = None,
    config: CodingPipelineConfig | None = None,
) -> dict[str, str | bool]:
    """Merge PR via gh CLI when auto-merge is on and QA passed."""
    cfg = config or get_coding_config()
    out: dict[str, str | bool] = {"merged": False, "reason": ""}

    if not should_auto_merge_repo(repo_slug, cfg):
        out["reason"] = "auto_merge_disabled"
        return out
    if not tests_passed:
        out["reason"] = "tests_failed"
        return out

    try:
        result = subprocess.run(
            [
                "gh",
                "pr",
                "merge",
                str(pr_number),
                "--merge",
                "--delete-branch",
            ],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            out["reason"] = (result.stderr or result.stdout or "gh pr merge failed")[:500]
            logger.warning("[CodingPipeline] gh pr merge #%s failed: %s", pr_number, out["reason"])
            return out
        out["merged"] = True
        out["reason"] = "merged"
        logger.info("[CodingPipeline] PR #%s merged (repo=%s)", pr_number, repo_slug or "?")
        subprocess.run(
            ["git", "pull", "origin", resolve_default_branch(repo_path)],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return out
    except Exception as exc:
        out["reason"] = str(exc)[:500]
        logger.error("[CodingPipeline] merge_pr_if_allowed: %s", exc)
        return out


def resolve_default_branch(repo_path: str) -> str:
    """Detect the repo's default branch (master/main) for diff/PR base."""
    for candidate in ("master", "main"):
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--verify", candidate],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if result.returncode == 0:
                return candidate
        except Exception:
            continue
    return "main"


def parse_pr_number(pr_url: str | None) -> int | None:
    if not pr_url:
        return None
    match = re.search(r"/pull/(\d+)", pr_url)
    return int(match.group(1)) if match else None
