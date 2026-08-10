"""Post-execution deliverable writes and per-agent validation."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from services.rnd_dispatch_playbooks import AgentPlaybook
from services.rnd_workspace import write_deliverable

logger = logging.getLogger(__name__)


def write_playbook_deliverables(
    slug: str,
    agent_id: str,
    output_text: str,
    playbook: AgentPlaybook,
) -> list[str]:
    """Ecrit les livrables sur disque selon le playbook (Option A : {pole}/{slug}/{filename})."""
    written: list[str] = []

    if len(playbook.files) == 1:
        try:
            filename = playbook.pole_relative_filename(0)
            path = write_deliverable(playbook.pole, slug, filename, output_text)
            written.append(playbook.files[0])
            logger.info("Livrable %s ecrit : %s", agent_id, path)
        except Exception as exc:
            logger.error("Ecriture livrable %s echoue : %s", agent_id, exc)
        return written

    parts = output_text.split("---SPLIT---")
    for i, filepath in enumerate(playbook.files):
        content = parts[i].strip() if i < len(parts) else output_text
        if not content:
            content = output_text
        filename = playbook.pole_relative_filename(i)
        try:
            path = write_deliverable(playbook.pole, slug, filename, content)
            written.append(filepath)
            logger.info("Livrable %s[%d] ecrit : %s", agent_id, i, path)
        except Exception as exc:
            logger.error("Ecriture livrable %s[%d] echoue : %s", agent_id, i, exc)

    return written


def create_dev_app_scaffold(slug: str, workspace_root: str) -> None:
    """Item 3 : cree un scaffold minimal pour dev_app dans app/{slug}/scaffold/."""
    scaffold_dir = Path(workspace_root) / "app" / slug / "scaffold"
    try:
        scaffold_dir.mkdir(parents=True, exist_ok=True)

        readme = (
            f"# {slug} — Scaffold Next.js\n\n"
            "Structure generee automatiquement par ALNUA Hub (Phase 9).\n\n"
            "## Demarrage\n"
            "```bash\nnpm install\nnpm run dev\n```\n\n"
            "## Stack\n"
            "- Next.js 14 App Router\n"
            "- TypeScript\n"
            "- Tailwind CSS\n"
            "- shadcn/ui\n"
        )
        (scaffold_dir / "README.md").write_text(readme, encoding="utf-8")

        github_token = os.environ.get("GITHUB_TOKEN", "").strip()
        coding_agent_note = (
            "true (GITHUB_TOKEN detecte — coding_agent peut initialiser le repo)"
            if github_token
            else "false (GITHUB_TOKEN absent — initialisation manuelle requise)"
        )

        pkg = (
            "{\n"
            f'  "name": "{slug}",\n'
            '  "version": "0.1.0",\n'
            '  "private": true,\n'
            f'  "description": "ALNUA project — coding_agent: {coding_agent_note}",\n'
            '  "scripts": {\n'
            '    "dev": "next dev",\n'
            '    "build": "next build",\n'
            '    "start": "next start",\n'
            '    "lint": "next lint"\n'
            '  },\n'
            '  "dependencies": {\n'
            '    "next": "14.x",\n'
            '    "react": "^18",\n'
            '    "react-dom": "^18"\n'
            '  },\n'
            '  "devDependencies": {\n'
            '    "typescript": "^5",\n'
            '    "@types/react": "^18",\n'
            '    "tailwindcss": "^3",\n'
            '    "autoprefixer": "^10",\n'
            '    "postcss": "^8"\n'
            '  }\n'
            "}\n"
        )
        (scaffold_dir / "package.json").write_text(pkg, encoding="utf-8")

        gitignore = (
            "node_modules/\n.next/\n.env\n.env.local\n.env*.local\n"
            "out/\nbuild/\ndist/\n*.log\n.DS_Store\n"
        )
        (scaffold_dir / ".gitignore").write_text(gitignore, encoding="utf-8")

        logger.info("dev_app scaffold cree : %s", scaffold_dir)
    except Exception as exc:
        logger.warning("create_dev_app_scaffold failed: %s", exc)


def validate_pm_step(db: Any, project_id: str | None, slug: str) -> bool:
    """Item 4 : apres handle_instruction PM, verifie le projet est cable en Hub."""
    if not project_id or not db:
        return False
    try:
        roadmap_rows = db.select("roadmap", filters={"project_id": project_id}, limit=1)
        if not roadmap_rows:
            try:
                roadmap_rows = db.select("milestones", filters={"project_id": project_id}, limit=1)
            except Exception:
                roadmap_rows = []
        if not roadmap_rows:
            logger.warning(
                "PM validation: no roadmap/milestones for project_id=%s slug=%s",
                project_id,
                slug,
            )
            return False

        tickets = db.select("tickets", filters={"project_id": project_id}, limit=1)
        if not tickets:
            logger.info(
                "PM validation: roadmap OK, no ticket yet for project_id=%s slug=%s",
                project_id,
                slug,
            )
        return True
    except Exception as exc:
        logger.warning("PM validation query failed: %s", exc)
        return False
