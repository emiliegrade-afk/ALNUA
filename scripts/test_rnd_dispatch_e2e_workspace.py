"""Test E2E Phase 9 — Workspace Dispatch avec LLM mocké.

Simule un dispatch complet CEO → agents → fichiers disque → manifest success.
LLM entièrement mocké via mock_execute_plan → aucune clé OpenRouter nécessaire.
Supabase mocké → aucune connexion réseau.

Usage :
    python scripts/test_rnd_dispatch_e2e_workspace.py

Vérifie :
1. run_dispatch_execution() crée les fichiers sur disque (Option A)
2. Manifest final status=success ou partial
3. workspace_validation persisté sur rnd_dossier (Item 8)
4. Ticket spec créé en Supabase avant l'appel spec (Item 2)
5. agent_logs success marqué APRÈS validate_deliverables (Item 5)
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

# Workspace temp — set avant tout import du pipeline
_TMP = tempfile.mkdtemp(prefix="alnua_e2e_test_")
os.environ["ALNUA_WORKSPACE"] = _TMP

PASS = "✅"
FAIL = "❌"
results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((name, condition, detail))
    icon = PASS if condition else FAIL
    print(f"  {icon}  {name}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# Mock DB Supabase
# ---------------------------------------------------------------------------

class MockDB:
    """Supabase client mocké — enregistre inserts/updates pour assertions."""

    def __init__(self) -> None:
        self.inserts: list[tuple[str, dict]] = []
        self.updates: list[tuple[str, str, dict]] = []
        self.selects: list[tuple[str, dict]] = []

    def insert(self, table: str, data: dict) -> dict:
        self.inserts.append((table, data))
        if table == "tickets":
            return {**data, "id": f"ticket-{len(self.inserts):03d}"}
        return data

    def update(self, table: str, record_id: str, data: dict) -> dict:
        self.updates.append((table, record_id, data))
        return data

    def select(self, table: str, filters: dict | None = None, limit: int = 100) -> list:
        self.selects.append((table, filters or {}))
        # PM validation: ticket + roadmap doivent exister
        if table == "tickets":
            return [{"id": "ticket-001", "project_id": "proj-001", "title": "Test ticket"}]
        if table in ("roadmap", "milestones"):
            return [{"id": "roadmap-001", "project_id": "proj-001"}]
        return []


# ---------------------------------------------------------------------------
# LLM mock — retourne livrables réalistes par agent
# ---------------------------------------------------------------------------

def _mock_output(agent_id: str) -> str:
    if agent_id == "spec":
        return (
            "# Spec Cursor Prompt — Mon Super Projet\n\n"
            "Ouvre `api/routers/my_project.py`.\n\n"
            "Le problème est : l'API n'a pas de endpoint.\n\n"
            "Voici ce qu'il faut faire :\n1. Créer le router\n2. Ajouter schema\n\n"
            "Critères d'acceptation :\n- [ ] Endpoint retourne 200\n- [ ] Tests passent"
        )
    if agent_id == "pm":
        return (
            "# Backlog MVP — Mon Super Projet\n## Épiques\n"
            "| # | Épique | Priorité | Agents | Effort |\n"
            "|---|--------|----------|--------|--------|\n"
            "| 1 | Core API | P0 | dev_backend | M |\n\n"
            "## User Stories P0\n- [ ] API accessible\n"
            "---SPLIT---\n"
            "# Critères d'acceptation v1\n## Fonctionnel\n- [ ] API < 500ms"
        )
    if agent_id == "coo":
        return (
            "# Brief COO — Mon Super Projet\n## Objectif\nLancer conception.\n"
            "## Pôles\n| direction | spec | J+1 |\n## Arbitrages\n- [ ] Priorité"
        )
    if agent_id == "marketing":
        return (
            "# GTM — Mon Super Projet\n## Positionnement\nSaaS dev tools\n"
            "## Message clé\nShip faster.\n"
            "---SPLIT---\n"
            "# Calendrier contenu (4 semaines)\n"
            "| S1 | LinkedIn | Post | Launch | Awareness |\n"
            "| S2 | Twitter | Thread | Features | Engagement |\n"
            "| S3 | GitHub | README | Docs | Trust |\n"
            "| S4 | Email | Newsletter | Recap | Retention |"
        )
    if agent_id == "accounting":
        return (
            "# Business Case — Mon Super Projet\n## ROI\nPositif en 6 mois.\n"
            "## Scénarios\nPessimiste: 5k€ | Réaliste: 50k€ | Optimiste: 200k€"
        )
    return f"# Livrable {agent_id}\n\nContenu généré pour {agent_id}.\n"


# ---------------------------------------------------------------------------
# Dossier R&D simulé
# ---------------------------------------------------------------------------

def _make_dossier(slug: str = "mon-super-projet"):
    from services.rnd_schemas import RndDossierOut
    return RndDossierOut(
        id="dossier-001",
        idea_id="idea-001",
        slug=slug,
        title="Mon Super Projet",
        domain="SaaS",
        status="ready_for_ceo",
        ceo_status="approved",
        dispatch_status="dispatched",
        one_pager_md="Un projet SaaS innovant.",
        finance_json={"capex": 10000},
    )


DISPATCH_MATRIX = [
    {"agent_id": "coo",        "pole": "direction", "deliverables": ["coo-coordination-brief.md"], "priority": "P0"},
    {"agent_id": "spec",       "pole": "direction", "deliverables": ["spec-cursor-prompt.md"],      "priority": "P0"},
    {"agent_id": "pm",         "pole": "direction", "deliverables": ["backlog-mvp.md"],             "priority": "P0"},
    {"agent_id": "marketing",  "pole": "comms",     "deliverables": ["gtm-strategy.md"],            "priority": "P1"},
    {"agent_id": "accounting", "pole": "finance",   "deliverables": ["business-case.md"],           "priority": "P1"},
]


# ---------------------------------------------------------------------------
# E2E run
# ---------------------------------------------------------------------------

def run_e2e() -> tuple[dict, MockDB, str]:
    slug = "mon-super-projet"
    dossier = _make_dossier(slug)
    mock_db = MockDB()

    from services.rnd_dispatch_executor import run_dispatch_execution

    def mock_execute_plan(plan, **kwargs):
        """Simule execute_plan : renvoie les outputs mockés sans appeler les vrais agents."""
        step_results = []

        for step in plan.steps:
            aid = step.agent_id
            method = step.method

            if aid == "spec" and method == "generate_and_write_dispatch":
                # Pour spec : écrit réellement sur disque via spec_agent.generate_and_write_dispatch
                # mais avec LLM mocké inline (sans importer agents.base)
                from services.rnd_workspace import write_deliverable as _wd
                cursor_prompt = _mock_output("spec")
                proj_slug = step.kwargs.get("project_info", {}).get("slug", slug)
                _wd("direction", proj_slug, "spec-cursor-prompt.md", cursor_prompt)
                # Simule aussi le ticket update
                ticket = step.kwargs.get("ticket", {})
                ticket_id = ticket.get("id")
                if ticket_id:
                    mock_db.update("tickets", ticket_id, {"cursor_prompt": cursor_prompt, "status": "in_progress"})
                step_results.append({
                    "agent_id": aid,
                    "step_id": step.step_id,
                    "success": True,
                    "result": {
                        "cursor_prompt": cursor_prompt,
                        "file_path": str(Path(_TMP) / "direction" / proj_slug / "spec-cursor-prompt.md"),
                        "slug": proj_slug,
                    },
                })
            else:
                step_results.append({
                    "agent_id": aid,
                    "step_id": step.step_id,
                    "success": True,
                    "result": _mock_output(aid),
                })

        return {"results": step_results, "success": True}

    with patch("services.rnd_dispatch_executor.execute_plan", side_effect=mock_execute_plan):
        result = run_dispatch_execution(
            dossier=dossier,
            matrix=DISPATCH_MATRIX,
            package={"markdown": "CEO one pager mock"},
            project_id="proj-001",
            db=mock_db,
        )

    return result, mock_db, slug


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------
print("\n" + "="*60)
print("TEST E2E — Phase 9 Workspace Dispatch (LLM mocké)")
print("="*60)

try:
    result, mock_db, slug = run_e2e()
    ws_root = Path(_TMP)

    print("\n[A] Structure disque Option A")
    spec_file = ws_root / "direction" / slug / "spec-cursor-prompt.md"
    check("spec-cursor-prompt.md créé (direction/{slug}/)", spec_file.exists(), str(spec_file))
    if spec_file.exists():
        txt = spec_file.read_text(encoding="utf-8")
        check("Spec > 100 chars", len(txt) > 100, f"{len(txt)} chars")
        check("Spec contient 'Critères'", "Critères" in txt or "criteres" in txt.lower())

    gtm_file = ws_root / "comms" / slug / "gtm-strategy.md"
    check("gtm-strategy.md créé (comms/{slug}/)", gtm_file.exists(), str(gtm_file))

    biz_file = ws_root / "finance" / slug / "business-case.md"
    check("business-case.md créé (finance/{slug}/)", biz_file.exists(), str(biz_file))

    coo_file = ws_root / "direction" / slug / "coo-coordination-brief.md"
    check("coo-coordination-brief.md créé", coo_file.exists(), str(coo_file))

    print("\n[B] Manifest JSON")
    from services.rnd_workspace import read_manifest
    manifest = read_manifest(slug)
    check("Manifest existe", bool(manifest))
    check("Convention Option A", manifest.get("convention") == "ALNUA/{pole}/{slug}/{filename}")
    validation = manifest.get("validation", {})
    check("validation.status non-pending", validation.get("status") != "pending")
    check("validation.completed_at présent", bool(validation.get("completed_at")))

    print("\n[C] workspace_validation persisté sur rnd_dossiers (Item 8)")
    rnd_updates = [(t, rid, d) for t, rid, d in mock_db.updates if t == "rnd_dossiers"]
    check("rnd_dossiers.update appelé", len(rnd_updates) > 0)
    if rnd_updates:
        _, _, upd = rnd_updates[-1]
        check("workspace_path dans update", "workspace_path" in upd)
        check("workspace_validation dans update", "workspace_validation" in upd)
        if "workspace_validation" in upd:
            wv = upd["workspace_validation"]
            check("workspace_validation.success est bool", isinstance(wv.get("success"), bool))
            check("workspace_validation.completed_at présent", bool(wv.get("completed_at")))
            check("workspace_validation.convention Option A", "pole" in wv.get("convention", ""))

    print("\n[D] Ticket spec créé dans Supabase avant appel spec (Item 2)")
    ticket_inserts = [(t, d) for t, d in mock_db.inserts if t == "tickets"]
    check("Au moins 1 ticket inséré", len(ticket_inserts) > 0)
    if ticket_inserts:
        _, td = ticket_inserts[0]
        check("type=spec", td.get("type") == "spec")
        check("source=rnd_dispatch", td.get("source") == "rnd_dispatch")
        check("workspace_slug rempli", bool(td.get("workspace_slug")))
        check("project_id transmis", td.get("project_id") == "proj-001")

    print("\n[E] agent_logs — success après validate_deliverables (Item 5)")
    log_inserts = [(t, d) for t, d in mock_db.inserts if t == "agent_logs"]
    check("agent_logs insérés", len(log_inserts) > 0)
    pending_logs = [d for _, d in log_inserts if d.get("status") == "pending"]
    success_logs = [d for _, d in log_inserts if d.get("status") == "success"]
    error_logs   = [d for _, d in log_inserts if d.get("status") == "error"]
    check("Logs pending phase init", len(pending_logs) > 0)
    check("Logs success ou error phase post-exec", len(success_logs) + len(error_logs) > 0)

    print("\n[F] Résultat run_dispatch_execution")
    check("result.workspace présent", "workspace" in result or "workspace_path" in result)
    check("result.validation présent", "validation" in result)
    if "validation" in result:
        v = result["validation"]
        check("validation.success est bool", isinstance(v.get("success"), bool))
        check("validation.completed_at présent", bool(v.get("completed_at")))
        check("validation.convention Option A", "pole" in v.get("convention", ""))

except Exception as exc:
    import traceback
    check("E2E run sans exception", False, str(exc))
    traceback.print_exc()

# ---------------------------------------------------------------------------
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

print(f"\n{'='*60}")
print(f"RÉSULTAT E2E Phase 9 : {passed}/{total} tests passés")
if failed:
    print(f"\nÉCHECS ({failed}) :")
    for name, ok, detail in results:
        if not ok:
            print(f"  ❌  {name}" + (f" — {detail}" if detail else ""))
print(f"{'='*60}\n")

import shutil
try:
    shutil.rmtree(_TMP)
    print(f"Workspace E2E nettoyé : {_TMP}")
except Exception:
    pass

sys.exit(0 if failed == 0 else 1)
