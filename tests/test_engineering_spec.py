"""Tests for engineering spec (Phase 3)."""

from __future__ import annotations

from services.engineering_spec import (
    EngineeringSpecResult,
    EngineeringTask,
    append_engineering_spec_to_package,
    build_dossier_context,
    _normalize_tasks,
)
from services.rnd_schemas import RndDossierOut, RndDossierSectionOut


def _sample_dossier() -> RndDossierOut:
    return RndDossierOut(
        id="dossier-001",
        idea_id="idea-001",
        slug="nuaway-mvp",
        title="NUAWAY",
        domain="app",
        branch="app",
        sections=[
            RndDossierSectionOut(
                id="s1",
                dossier_id="dossier-001",
                section_key="problem",
                title="Problème",
                content_md="Vanlifers need safe overnight spots.",
                status="validated",
            ),
            RndDossierSectionOut(
                id="s2",
                dossier_id="dossier-001",
                section_key="mvp",
                title="MVP",
                content_md="Map + favorites + community reviews.",
                status="validated",
            ),
        ],
    )


def test_build_dossier_context_includes_sections():
    ctx = build_dossier_context(_sample_dossier())
    assert "NUAWAY" in ctx
    assert "problem" in ctx
    assert "Vanlifers" in ctx


def test_normalize_tasks_skips_invalid():
    raw = [
        {"id": "T-001", "title": "Setup Expo"},
        {"title": ""},
        "not-a-dict",
    ]
    tasks = _normalize_tasks(raw)
    assert len(tasks) == 1
    assert tasks[0].id == "T-001"


def test_append_engineering_spec_to_package():
    package = {"version": 2, "markdown": "# CEO\n\n---\n", "blocks": {}}
    spec = EngineeringSpecResult(
        engineering_spec_md="## 10. Product Engineering Spec\n\n### 10.1 Contexte",
        task_breakdown=[
            EngineeringTask(id="T-001", title="Init repo", priority="P0", sprint=1),
        ],
    )
    updated = append_engineering_spec_to_package(package, spec)
    assert "## 10." in updated["markdown"]
    assert updated["engineering_spec"]["task_breakdown"][0]["title"] == "Init repo"
    assert updated["version"] == 3
    assert "engineering_spec" in updated["blocks"]
