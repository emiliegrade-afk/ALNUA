"""Product Engineering Spec (CEO package §10) — Léon (spec) + adversarial QA."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from agents.base import LLMClient, parse_json_response
from config.agent_personas import persona_prompt_intro
from services.adversarial_spec import debate_spec
from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)

ENGINEERING_SPEC_OUTLINE = """
## 10. Product Engineering Spec (PRD technique)

Structure OBLIGATOIRE :
### 10.1 Contexte & objectifs
### 10.2 Écrans / parcours utilisateur
### 10.3 User stories (format : En tant que… je veux… afin de…)
### 10.4 Contrat API (méthode, route, auth, payload, réponse)
### 10.5 Schéma Supabase (tables, colonnes clés, RLS)
### 10.6 Tests E2E / critères d'acceptation
### 10.7 Task breakdown JSON (liste ordonnée de tâches agent-ready)
"""

_SPEC_INTRO = persona_prompt_intro("spec", role="Spec Rédacteur")
_PM_INTRO = persona_prompt_intro("pm", role="PM")

_ENGINEERING_SPEC_SYSTEM = _SPEC_INTRO + """.
Tu produis la section 10 « Product Engineering Spec » d'un dossier CEO validé.

Stack par défaut pour apps voyage / NUAWAY : React Native Expo + Supabase + Mapbox.
Stack Hub ALNUA : Python FastAPI + Next.js + Supabase.

Réponds UNIQUEMENT en JSON valide :
{
  "engineering_spec_md": "markdown complet section 10 (### 10.1 à 10.6)",
  "stack": "react_native_expo|nextjs|python_fastapi|godot",
  "screens": [{"id": "screen_id", "name": "...", "route": "...", "description": "..."}],
  "user_stories": [{"id": "US-001", "story": "En tant que...", "acceptance": ["..."]}],
  "api_contract": [{"method": "GET", "route": "/api/...", "auth": "...", "description": "..."}],
  "supabase_tables": [{"name": "...", "columns": ["..."], "rls": "..."}],
  "e2e_tests": [{"id": "E2E-001", "scenario": "...", "steps": ["..."]}],
  "task_breakdown": [
    {
      "id": "T-001",
      "title": "Court titre actionnable",
      "description": "Ce qui doit être implémenté",
      "stack": "react_native_expo",
      "files_create": ["path/to/new.tsx"],
      "files_modify": ["path/to/existing.ts"],
      "tests": ["tests/test_x.py"],
      "priority": "P0|P1|P2",
      "sprint": 1,
      "depends_on": [],
      "agent_id": "dev_app"
    }
  ]
}

Règles :
- 40 à 80 tâches pour un MVP ambitieux (NUAWAY-like), 15-25 pour un petit scope.
- Chaque tâche = 1 PR / 1 issue agent (2-4h dev agent).
- Titres commençant par un verbe d'action.
- depends_on = ids de tâches du même breakdown.
- Ne pas inventer de features hors scope dossier."""

_TASK_BREAKDOWN_PM_SYSTEM = _PM_INTRO + """.
Tu affines le task_breakdown JSON d'une engineering spec pour publication GitHub.

Réponds UNIQUEMENT en JSON :
{
  "task_breakdown": [ ... même structure, champs id/title/description/stack/files_create/files_modify/tests/priority/sprint/depends_on/agent_id ... ],
  "sprint_plan": [{"sprint": 1, "goal": "...", "task_ids": ["T-001"]}],
  "notes": "arbitrages PM"
}

Règles :
- Garder l'ordre logique (setup → auth → core features → polish).
- P0 = bloquant MVP, P1 = important, P2 = nice-to-have.
- Ne pas fusionner plusieurs features en une seule tâche."""


class EngineeringTask(BaseModel):
    id: str
    title: str
    description: str = ""
    stack: str = "react_native_expo"
    files_create: list[str] = Field(default_factory=list)
    files_modify: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    priority: str = "P1"
    sprint: int = 1
    depends_on: list[str] = Field(default_factory=list)
    agent_id: str = "dev_app"


class EngineeringSpecResult(BaseModel):
    engineering_spec_md: str
    stack: str = "react_native_expo"
    screens: list[dict[str, Any]] = Field(default_factory=list)
    user_stories: list[dict[str, Any]] = Field(default_factory=list)
    api_contract: list[dict[str, Any]] = Field(default_factory=list)
    supabase_tables: list[dict[str, Any]] = Field(default_factory=list)
    e2e_tests: list[dict[str, Any]] = Field(default_factory=list)
    task_breakdown: list[EngineeringTask] = Field(default_factory=list)
    sprint_plan: list[dict[str, Any]] = Field(default_factory=list)
    qa_verdict: str | None = None
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


def _section_map(dossier: RndDossierOut) -> dict[str, str]:
    return {s.section_key: s.content_md or "" for s in dossier.sections}


def build_dossier_context(dossier: RndDossierOut, *, ceo_package: dict[str, Any] | None = None) -> str:
    """Aggregate dossier sections + CEO package for LLM context."""
    sections = _section_map(dossier)
    parts = [
        f"# Dossier : {dossier.title}",
        f"Slug : {dossier.slug} · Branche : {dossier.branch or dossier.domain}",
        f"Tagline : {dossier.tagline or '—'}",
        "",
    ]
    for key in (
        "problem", "solution", "market", "mvp", "feasibility",
        "business_case", "risks", "decision",
    ):
        body = (sections.get(key) or "").strip()
        if body:
            parts.extend([f"## {key}", body[:4000], ""])

    if ceo_package:
        rec = ceo_package.get("recommendation")
        if rec:
            parts.append(f"Recommandation comité : {rec}")
        matrix = ceo_package.get("dispatch_matrix") or []
        if matrix:
            parts.append("### Dispatch matrix")
            for row in matrix[:8]:
                parts.append(
                    f"- {row.get('pole')} / {row.get('agent_id')} : "
                    f"{', '.join(row.get('deliverables') or [])}"
                )
    return "\n".join(parts)


def _normalize_tasks(raw_tasks: list[Any]) -> list[EngineeringTask]:
    tasks: list[EngineeringTask] = []
    for i, item in enumerate(raw_tasks or []):
        if not isinstance(item, dict):
            continue
        task_id = str(item.get("id") or f"T-{i + 1:03d}")
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        try:
            tasks.append(
                EngineeringTask(
                    id=task_id,
                    title=title,
                    description=str(item.get("description") or ""),
                    stack=str(item.get("stack") or "react_native_expo"),
                    files_create=[str(f) for f in (item.get("files_create") or [])],
                    files_modify=[str(f) for f in (item.get("files_modify") or [])],
                    tests=[str(t) for t in (item.get("tests") or [])],
                    priority=str(item.get("priority") or "P1"),
                    sprint=int(item.get("sprint") or 1),
                    depends_on=[str(d) for d in (item.get("depends_on") or [])],
                    agent_id=str(item.get("agent_id") or "dev_app"),
                )
            )
        except (TypeError, ValueError):
            continue
    return tasks


def generate_engineering_spec(
    dossier: RndDossierOut,
    *,
    ceo_package: dict[str, Any] | None = None,
    llm: LLMClient | None = None,
    debate_rounds: int = 1,
    refine_with_pm: bool = True,
) -> EngineeringSpecResult:
    """
    Generate §10 Product Engineering Spec via Léon (spec) + optional QA debate + PM refine.
    """
    client = llm or LLMClient()
    context = build_dossier_context(dossier, ceo_package=ceo_package)
    pkg = ceo_package or {}

    prompt = (
        f"{ENGINEERING_SPEC_OUTLINE}\n\n"
        f"--- DOSSIER SOURCE ---\n{context[:24000]}\n\n"
        "Produis la section 10 complète + task_breakdown JSON."
    )
    raw = client.complete(
        _ENGINEERING_SPEC_SYSTEM,
        prompt,
        agent_id="spec",
        temperature=0.35,
        method_name="generate_engineering_spec",
    )
    parsed = parse_json_response(raw)
    spec_md = str(parsed.get("engineering_spec_md") or "")
    tasks = _normalize_tasks(parsed.get("task_breakdown") or [])

    qa_verdict: str | None = None
    if debate_rounds > 0 and spec_md:
        try:
            debate = debate_spec(
                spec_text=spec_md,
                context=f"Engineering spec — {dossier.title}",
                rounds=debate_rounds,
            )
            consensus = str(debate.get("consensus_spec") or spec_md)
            if len(consensus) > 200:
                spec_md = consensus
            qa_verdict = str(debate.get("final_verdict") or "revise")
        except Exception as exc:
            logger.warning("adversarial_spec failed: %s", exc)

    sprint_plan: list[dict[str, Any]] = []
    if refine_with_pm and tasks:
        try:
            pm_raw = client.complete(
                _TASK_BREAKDOWN_PM_SYSTEM,
                json.dumps(
                    {
                        "dossier": dossier.title,
                        "stack": parsed.get("stack"),
                        "task_breakdown": [t.model_dump() for t in tasks],
                    },
                    ensure_ascii=False,
                ),
                agent_id="pm",
                temperature=0.25,
                method_name="refine_task_breakdown",
            )
            pm_parsed = parse_json_response(pm_raw)
            refined = _normalize_tasks(pm_parsed.get("task_breakdown") or [])
            if refined:
                tasks = refined
            sprint_plan = list(pm_parsed.get("sprint_plan") or [])
        except Exception as exc:
            logger.warning("PM refine failed: %s", exc)

    return EngineeringSpecResult(
        engineering_spec_md=spec_md,
        stack=str(parsed.get("stack") or "react_native_expo"),
        screens=list(parsed.get("screens") or []),
        user_stories=list(parsed.get("user_stories") or []),
        api_contract=list(parsed.get("api_contract") or []),
        supabase_tables=list(parsed.get("supabase_tables") or []),
        e2e_tests=list(parsed.get("e2e_tests") or []),
        task_breakdown=tasks,
        sprint_plan=sprint_plan,
        qa_verdict=qa_verdict,
    )


def append_engineering_spec_to_package(
    package: dict[str, Any],
    spec: EngineeringSpecResult,
) -> dict[str, Any]:
    """Merge §10 into CEO package JSON + markdown."""
    md = str(package.get("markdown") or "")
    section = spec.engineering_spec_md.strip()
    if section and "## 10." not in md:
        md = md.rstrip() + "\n\n---\n\n" + section + "\n"
    elif section:
        # Replace existing §10 block if present
        head, _, _tail = md.partition("## 10.")
        if head:
            md = head.rstrip() + "\n\n---\n\n" + section + "\n"

    updated = {
        **package,
        "version": max(int(package.get("version") or 2), 3),
        "markdown": md,
        "engineering_spec": spec.to_dict(),
        "engineering_spec_generated_at": spec.generated_at,
    }
    blocks = dict(package.get("blocks") or {})
    blocks["engineering_spec"] = {
        "title": "10. Product Engineering Spec",
        "content_md": section,
    }
    updated["blocks"] = blocks
    return updated
