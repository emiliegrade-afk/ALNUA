"""App factory — brief → MVP plan → GitHub issues → coding pipeline (Phase 2)."""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from agents.base import LLMClient, log_agent_action, parse_json_response
from config.github_repos import GitHubRepoTarget, annotate_issue, resolve_target
from config.paths import get_hub_repo_path
from services.app_registry import AppRegistryUpsert, upsert_app
from services.coding_pipeline import DevStack
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)

_FACTORY_STACK = Literal["nextjs", "expo"]
_RUNS: dict[str, dict[str, Any]] = {}
_PLANS_DIR = get_hub_repo_path() / "data" / "app_factory"

GITHUB_API = "https://api.github.com"


class FactoryTask(BaseModel):
    title: str
    description: str
    files_to_create: list[str] = Field(default_factory=list)
    files_to_modify: list[str] = Field(default_factory=list)
    tests_to_pass: list[str] = Field(default_factory=list)
    priority: str = "P0"


class AppFactoryRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    brief: str = Field(..., min_length=10, max_length=8000)
    stack: _FACTORY_STACK = "nextjs"
    slug: str = ""
    github_repo: str = ""
    local_path: str = ""
    branch: Literal["app", "gaming", "robotics", "other"] = "app"
    auto_run_pipeline: bool = True


def _slugify(value: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return s or "app"


def _default_local_path(slug: str) -> str:
    parent = get_hub_repo_path().parent
    return str(parent / slug)


def _stack_value(stack: _FACTORY_STACK) -> str:
    return DevStack.NEXTJS.value if stack == "nextjs" else DevStack.REACT_NATIVE_EXPO.value


def _github_headers() -> dict[str, str]:
    from skills.skill_gh_issues import get_headers

    return get_headers()


def create_issue_on_repo(
    target: GitHubRepoTarget,
    *,
    title: str,
    body: str,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a GitHub issue and return annotated issue dict."""
    with httpx.Client() as client:
        resp = client.post(
            f"{GITHUB_API}/repos/{target.github_repo}/issues",
            headers=_github_headers(),
            json={
                "title": title,
                "body": body,
                "labels": labels or [],
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        return annotate_issue(resp.json(), target)


def format_issue_body(task: FactoryTask, stack: _FACTORY_STACK) -> str:
    """Markdown body parsed by skill_gh_issues.issue_to_spec."""
    create_lines = "\n".join(f"- {p}" for p in task.files_to_create) or "- <!-- à définir -->"
    modify_lines = "\n".join(f"- {p}" for p in task.files_to_modify) or "- <!-- aucun -->"
    test_lines = "\n".join(f"- {t}" for t in task.tests_to_pass) or "- npm run build"
    return (
        f"## Description\n{task.description.strip()}\n\n"
        f"## Stack\n{_stack_value(stack)}\n\n"
        f"## Fichiers à créer\n{create_lines}\n\n"
        f"## Fichiers à modifier\n{modify_lines}\n\n"
        f"## Tests\n{test_lines}\n"
    )


def _fallback_plan(name: str, brief: str, stack: _FACTORY_STACK) -> list[FactoryTask]:
    """Deterministic MVP when LLM unavailable (tests / dry-run)."""
    if stack == "expo":
        return [
            FactoryTask(
                title=f"{name} — scaffold Expo",
                description=(
                    f"Initialiser l'app Expo pour {name}.\n\nBrief:\n{brief[:500]}"
                ),
                files_to_create=["app.json", "App.tsx", "package.json", "tsconfig.json"],
                tests_to_pass=["npx expo export --platform web"],
                priority="P0",
            ),
            FactoryTask(
                title=f"{name} — écran d'accueil MVP",
                description="Écran principal avec navigation de base et thème ALNUA.",
                files_to_create=["src/screens/HomeScreen.tsx", "src/theme/colors.ts"],
                files_to_modify=["App.tsx"],
                tests_to_pass=["npx expo start --non-interactive"],
                priority="P1",
            ),
        ]
    return [
        FactoryTask(
            title=f"{name} — scaffold Next.js",
            description=(
                f"Initialiser le projet Next.js App Router pour {name}.\n\nBrief:\n{brief[:500]}"
            ),
            files_to_create=[
                "package.json",
                "next.config.mjs",
                "tsconfig.json",
                "src/app/layout.tsx",
                "src/app/page.tsx",
                "src/app/globals.css",
            ],
            tests_to_pass=["npm run build"],
            priority="P0",
        ),
        FactoryTask(
            title=f"{name} — page MVP + layout",
            description="Page d'accueil MVP alignée sur le brief, Tailwind + structure Hub.",
            files_to_create=["src/components/home-hero.tsx"],
            files_to_modify=["src/app/page.tsx", "src/app/layout.tsx"],
            tests_to_pass=["npm run lint", "npm run build"],
            priority="P1",
        ),
    ]


@trace_agent("spec_agent")
def generate_factory_plan(
    name: str,
    brief: str,
    stack: _FACTORY_STACK,
    *,
    dry_run: bool = False,
) -> list[FactoryTask]:
    """Léon + Sam lightweight — JSON task breakdown for MVP."""
    if dry_run or os.getenv("APP_FACTORY_DRY_RUN", "").lower() in ("1", "true", "yes"):
        return _fallback_plan(name, brief, stack)

    stack_label = "Next.js 14 App Router" if stack == "nextjs" else "React Native Expo"
    system = """Tu es Léon (Spec) + Sam (PM) d'ALNUA.
Transforme un brief produit en plan MVP codable par dev_app.
Réponds UNIQUEMENT en JSON valide:
{
  "tasks": [
    {
      "title": "string",
      "description": "string (détaillé, actionnable)",
      "files_to_create": ["chemins/relatifs"],
      "files_to_modify": ["chemins/relatifs"],
      "tests_to_pass": ["commandes shell"],
      "priority": "P0|P1"
    }
  ]
}
Règles: 2 à 4 tâches max, la première = scaffold, chemins réalistes, pas de blabla."""
    prompt = (
        f"App: {name}\nStack: {stack_label}\n\nBrief:\n{brief}\n\n"
        "Génère le plan MVP (scaffold + features P0)."
    )
    llm = LLMClient()
    try:
        raw = llm.complete(system, prompt, agent_id="spec_agent", temperature=0.35)
        data = parse_json_response(raw)
        tasks_raw = data.get("tasks") if isinstance(data, dict) else None
        if not isinstance(tasks_raw, list) or not tasks_raw:
            raise ValueError("tasks missing")
        tasks = [FactoryTask.model_validate(t) for t in tasks_raw[:4]]
        return tasks
    except Exception as exc:
        logger.warning("generate_factory_plan LLM fallback: %s", exc)
        return _fallback_plan(name, brief, stack)


def ensure_local_scaffold(slug: str, stack: _FACTORY_STACK, local_path: Path) -> bool:
    """Create minimal on-disk scaffold when repo folder is empty."""
    if local_path.exists() and any(local_path.iterdir()):
        return False
    local_path.mkdir(parents=True, exist_ok=True)
    readme = (
        f"# {slug}\n\nScaffold ALNUA App Factory (Phase 2).\n\n"
        f"Stack: {stack}\n"
    )
    (local_path / "README.md").write_text(readme, encoding="utf-8")
    if stack == "expo":
        (local_path / "app.json").write_text(
            json.dumps({"expo": {"name": slug, "slug": slug, "version": "1.0.0"}}, indent=2),
            encoding="utf-8",
        )
        (local_path / "package.json").write_text(
            json.dumps(
                {
                    "name": slug,
                    "version": "0.1.0",
                    "private": True,
                    "main": "expo/AppEntry.js",
                    "scripts": {"start": "expo start"},
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    else:
        (local_path / "package.json").write_text(
            json.dumps(
                {
                    "name": slug,
                    "version": "0.1.0",
                    "private": True,
                    "scripts": {
                        "dev": "next dev",
                        "build": "next build",
                        "lint": "next lint",
                    },
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        src_app = local_path / "src" / "app"
        src_app.mkdir(parents=True, exist_ok=True)
        (src_app / "page.tsx").write_text(
            'export default function Home() {\n  return <main>MVP</main>;\n}\n',
            encoding="utf-8",
        )
    return True


def _persist_plan(slug: str, plan: list[FactoryTask]) -> Path:
    _PLANS_DIR.mkdir(parents=True, exist_ok=True)
    path = _PLANS_DIR / f"{slug}.json"
    payload = {
        "slug": slug,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "tasks": [t.model_dump() for t in plan],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def register_factory_app(req: AppFactoryRequest, slug: str) -> dict[str, Any]:
    local = req.local_path.strip() or _default_local_path(slug)
    stack_label = "Next.js" if req.stack == "nextjs" else "Expo"
    entry = upsert_app(
        AppRegistryUpsert(
            slug=slug,
            name=req.name.strip(),
            branch=req.branch,
            github_repo=req.github_repo.strip(),
            local_path=local,
            description=req.brief[:500],
            stack=stack_label,
            enabled=True,
        )
    )
    return entry.model_dump()


def run_app_factory_sync(
    run_id: str,
    req: AppFactoryRequest,
    *,
    dry_run: bool = False,
) -> None:
    """Background worker — updates _RUNS[run_id] in place."""
    run = _RUNS[run_id]
    slug = _slugify(req.slug or req.name)

    def log(msg: str) -> None:
        run["log"].append(msg)
        logger.info("[AppFactory %s] %s", run_id[:8], msg)

    try:
        run["status"] = "planning"
        run["progress"] = 10
        log(f"Plan MVP pour « {req.name} » ({req.stack})")

        plan = generate_factory_plan(req.name, req.brief, req.stack, dry_run=dry_run)
        run["plan"] = [t.model_dump() for t in plan]
        run["progress"] = 25
        _persist_plan(slug, plan)
        log(f"{len(plan)} tâches générées")

        run["status"] = "registering"
        app_entry = register_factory_app(req, slug)
        run["app"] = app_entry
        run["slug"] = slug
        run["progress"] = 40
        log(f"App enregistrée: {slug}")

        local_path = Path(app_entry.get("local_path") or _default_local_path(slug))
        if ensure_local_scaffold(slug, req.stack, local_path):
            log(f"Scaffold local créé: {local_path}")

        github_repo = (req.github_repo or app_entry.get("github_repo") or "").strip()
        if not github_repo:
            run["status"] = "needs_github"
            run["progress"] = 100
            log("Pas de repo GitHub — ajoute github_repo dans Mes apps puis relance pipeline")
            return

        if dry_run:
            run["status"] = "completed"
            run["progress"] = 100
            log("Dry-run — issues non créées")
            return

        run["status"] = "creating_issues"
        target = resolve_target(repo_slug=slug)
        issues: list[dict[str, Any]] = []
        for i, task in enumerate(plan):
            labels = ["agent-ready"] if i == 0 else ["backlog"]
            body = format_issue_body(task, req.stack)
            issue = create_issue_on_repo(
                target,
                title=task.title,
                body=body,
                labels=labels,
            )
            issues.append(
                {
                    "number": issue["number"],
                    "title": issue["title"],
                    "url": issue.get("html_url", ""),
                    "agent_ready": i == 0,
                }
            )
            log(f"Issue #{issue['number']}: {task.title}")

        run["issues"] = issues
        run["progress"] = 70

        if req.auto_run_pipeline and issues:
            run["status"] = "coding"
            log(f"Lancement pipeline sur issue #{issues[0]['number']}")
            from skills.skill_gh_issues import get_issue, process_issue

            issue_full = get_issue(issues[0]["number"], repo_slug=slug)
            repo_path = str(target.local_path)
            result = process_issue(issue_full, repo_path, None)
            run["pipeline"] = result
            if result.get("success"):
                run["status"] = "completed"
                run["progress"] = 100
                log(f"PR créée: {result.get('pr_url', '')[:80]}")
            else:
                run["status"] = "pipeline_failed"
                run["progress"] = 100
                log(f"Pipeline échoué: {result.get('error', 'unknown')}")
        else:
            run["status"] = "completed"
            run["progress"] = 100
            log("Issues créées — pipeline non lancé")

        try:
            from database.supabase_client import get_supabase

            log_agent_action(
                get_supabase(),
                "dev_app",
                "app_factory_run",
                input_summary=f"{slug}: {req.name[:60]}",
                output_summary=run["status"],
            )
        except Exception:
            pass
    except Exception as exc:
        logger.exception("App factory run %s failed", run_id)
        run["status"] = "failed"
        run["progress"] = 100
        run["error"] = str(exc)
        log(f"ERREUR: {exc}")


def start_app_factory_run(req: AppFactoryRequest, *, dry_run: bool = False) -> dict[str, Any]:
    """Queue a factory run; caller must schedule run_app_factory_sync in background."""
    run_id = str(uuid.uuid4())
    _RUNS[run_id] = {
        "run_id": run_id,
        "status": "queued",
        "progress": 0,
        "log": [],
        "slug": _slugify(req.slug or req.name),
        "started_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
    }
    return {"run_id": run_id, "status": "queued", "slug": _RUNS[run_id]["slug"]}


def get_factory_run(run_id: str) -> dict[str, Any] | None:
    return _RUNS.get(run_id)


def list_factory_runs(limit: int = 20) -> list[dict[str, Any]]:
    items = sorted(
        _RUNS.values(),
        key=lambda r: r.get("started_at", ""),
        reverse=True,
    )
    return items[:limit]


def trigger_pipeline_for_run(run_id: str) -> dict[str, Any]:
    """Manually start coding pipeline on first agent-ready issue."""
    run = _RUNS.get(run_id)
    if not run:
        raise ValueError("Run introuvable")
    slug = run.get("slug") or ""
    issues = run.get("issues") or []
    if not issues:
        raise ValueError("Aucune issue — configure github_repo et relance la factory")
    from skills.skill_gh_issues import get_issue, process_issue

    target = resolve_target(repo_slug=slug)
    issue_full = get_issue(issues[0]["number"], repo_slug=slug)
    result = process_issue(issue_full, str(target.local_path), None)
    run["pipeline"] = result
    run["status"] = "completed" if result.get("success") else "pipeline_failed"
    return result
