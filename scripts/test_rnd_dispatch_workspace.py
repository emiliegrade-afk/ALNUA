"""Test Phase 9 — Workspace Dispatch + Livrables Persistants (Option A).

Convention testée : ALNUA_WORKSPACE/{pole}/{slug}/{filename}
Manifest : ALNUA_WORKSPACE/{slug}.manifest.json (racine)

Usage :
    python scripts/test_rnd_dispatch_workspace.py

Ce script NE nécessite PAS de Supabase ni de clé OpenRouter.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

# ── Ajoute la racine au PYTHONPATH pour les imports relatifs
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

# Pointe le workspace sur un dossier temp pour ne pas polluer C:\Dev\ALNUA
_TMP = tempfile.mkdtemp(prefix="alnua_ws_test_")
os.environ["ALNUA_WORKSPACE"] = _TMP  # doit être set avant l'import du module

# Import après avoir set la var d'env
from services.rnd_workspace import (  # noqa: E402
    WORKSPACE_POLES,
    all_deliverables_present,
    finalize_manifest,
    init_manifest,
    init_project_workspace,
    missing_deliverables,
    pole_path,
    read_manifest,
    update_manifest_agent,
    validate_deliverables,
    write_deliverable,
)
from services.rnd_dispatch_playbooks import (  # noqa: E402
    all_required_files,
    build_instruction_with_paths,
    get_playbook,
)
from services.rnd_dispatch_executor import _extract_text_output  # noqa: E402

SLUG = "test-project-phase9"
PASS = "✅"
FAIL = "❌"
results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((name, condition, detail))
    icon = PASS if condition else FAIL
    print(f"  {icon}  {name}" + (f" — {detail}" if detail else ""))


# ---------------------------------------------------------------------------
# 1. init_project_workspace — Option A : {pole}/{slug}/
# ---------------------------------------------------------------------------
print("\n[1] init_project_workspace() — Option A : {pole}/{slug}/")
ws_root = Path(_TMP)
paths = init_project_workspace(SLUG)

check("Retourne un dict", isinstance(paths, dict))
check("Contient tous les poles", set(paths.keys()) == set(WORKSPACE_POLES))

for pole in WORKSPACE_POLES:
    expected = ws_root / pole / SLUG
    check(
        f"  {pole}/{SLUG}/ créé",
        expected.is_dir(),
        str(expected),
    )
    if pole in paths:
        check(f"  dict[{pole}] == attendu", paths[pole] == expected)

# Idempotence
paths2 = init_project_workspace(SLUG)
check("Idempotence (2ème appel)", paths2 == paths)


# ---------------------------------------------------------------------------
# 2. write_deliverable — pole, slug, filename, content
# ---------------------------------------------------------------------------
print("\n[2] write_deliverable(pole, slug, filename, content) — Option A")
content_txt = "# Spec Cursor\n\nContenu de test.\n\n## Étapes\n1. Step one\n"
path = write_deliverable("direction", SLUG, "spec-cursor-prompt.md", content_txt)

check("Fichier écrit sur disque", path.exists(), str(path))
check("Contenu correct", path.read_text(encoding="utf-8") == content_txt)
# Option A : {ws}/direction/{slug}/spec-cursor-prompt.md
expected_path = ws_root / "direction" / SLUG / "spec-cursor-prompt.md"
check("Path Option A correct", path == expected_path, str(path))
check("Parent == direction/{slug}/", path.parent == ws_root / "direction" / SLUG)


# ---------------------------------------------------------------------------
# 3. pole_path
# ---------------------------------------------------------------------------
print("\n[3] pole_path()")
pp = pole_path("direction", SLUG)
check("pole_path direction correct", pp == ws_root / "direction" / SLUG, str(pp))
check("pole_path app correct", pole_path("app", SLUG) == ws_root / "app" / SLUG)


# ---------------------------------------------------------------------------
# 4. validate_deliverables — format "pole/filename"
# ---------------------------------------------------------------------------
print("\n[4] validate_deliverables() — format 'pole/filename'")
checks = validate_deliverables(SLUG, [
    "direction/spec-cursor-prompt.md",   # existe (écrit ci-dessus)
    "direction/backlog-mvp.md",          # n'existe pas encore
])
check("Fichier présent détecté", checks["direction/spec-cursor-prompt.md"] is True)
check("Fichier absent détecté", checks["direction/backlog-mvp.md"] is False)

missing = missing_deliverables(SLUG, [
    "direction/spec-cursor-prompt.md",
    "direction/backlog-mvp.md",
])
check("missing_deliverables retourne [backlog-mvp.md]", missing == ["direction/backlog-mvp.md"])

check("all_deliverables_present False quand manquant", not all_deliverables_present(
    SLUG, ["direction/spec-cursor-prompt.md", "direction/backlog-mvp.md"]
))

# Écrit le fichier manquant et re-vérifie
write_deliverable("direction", SLUG, "backlog-mvp.md", "# Backlog MVP\n- P0: Feature A\n")
check("all_deliverables_present True après écriture", all_deliverables_present(
    SLUG, ["direction/spec-cursor-prompt.md", "direction/backlog-mvp.md"]
))


# ---------------------------------------------------------------------------
# 5. Manifest JSON — racine ws/{slug}.manifest.json
# ---------------------------------------------------------------------------
print("\n[5] Manifest JSON — racine workspace")
fake_matrix = [
    {"agent_id": "spec", "pole": "direction"},
    {"agent_id": "pm", "pole": "direction"},
    {"agent_id": "marketing", "pole": "comms"},
]
manifest = init_manifest(SLUG, "Test Project Phase9", ws_root, fake_matrix)
check("Manifest retourné est un dict", isinstance(manifest, dict))
check("Convention Option A dans manifest", manifest.get("convention") == "ALNUA/{pole}/{slug}/{filename}")
check("Manifest a poles", "poles" in manifest and len(manifest["poles"]) == len(WORKSPACE_POLES))
check("Manifest a agents", "agents" in manifest and "spec" in manifest["agents"])

# Manifest à la racine du workspace (pas dans le projet)
manifest_file = ws_root / f"{SLUG}.manifest.json"
check("Manifest écrit à la RACINE workspace", manifest_file.exists(), str(manifest_file))
# Vérifie que le manifest N'est PAS à {slug}/{slug}.manifest.json (Option B serait faux)
wrong_path = ws_root / SLUG / f"{SLUG}.manifest.json"
check("Manifest PAS dans sous-dossier {slug}/", not wrong_path.exists())

# Pole paths dans le manifest correspondent à Option A
for pole in WORKSPACE_POLES:
    expected_pole_path = str(ws_root / pole / SLUG)
    actual = manifest.get("poles", {}).get(pole, {}).get("path", "")
    check(f"  poles.{pole}.path == Option A", actual == expected_pole_path)

# read_manifest
m = read_manifest(SLUG)
check("read_manifest lit correctement", m.get("slug") == SLUG)
check("read_manifest title correct", m.get("title") == "Test Project Phase9")

# update_manifest_agent
update_manifest_agent(SLUG, "spec", status="success", files=["direction/spec-cursor-prompt.md"])
m2 = read_manifest(SLUG)
check("update_manifest_agent status=success", m2["agents"]["spec"]["status"] == "success")
check(
    "update_manifest_agent files rempli",
    "direction/spec-cursor-prompt.md" in m2["agents"]["spec"]["deliverables"],
)

update_manifest_agent(SLUG, "pm", status="error", error="LLM timeout")
m3 = read_manifest(SLUG)
check("update_manifest_agent error stocké", "error" in m3["agents"]["pm"])

# finalize_manifest
finalize_manifest(SLUG, success=False, missing=["direction/acceptance-criteria-v1.md"])
m4 = read_manifest(SLUG)
check("finalize_manifest status=partial", m4["validation"]["status"] == "partial")
check(
    "finalize_manifest missing_files",
    "direction/acceptance-criteria-v1.md" in m4["validation"]["missing_files"],
)
check("finalize_manifest completed_at non-null", bool(m4["validation"]["completed_at"]))

finalize_manifest(SLUG, success=True)
m5 = read_manifest(SLUG)
check("finalize_manifest success", m5["validation"]["status"] == "success")


# ---------------------------------------------------------------------------
# 6. Playbooks
# ---------------------------------------------------------------------------
print("\n[6] Playbooks")
for agent_id in ["spec", "pm", "marketing", "accounting", "dev_app", "coo"]:
    pb = get_playbook(agent_id)
    check(f"Playbook {agent_id} existe", pb is not None)
    if pb:
        check(f"  {agent_id}.pole non-vide", bool(pb.pole))
        check(f"  {agent_id}.files non-vide", len(pb.files) > 0)
        check(f"  {agent_id}.template contient {{title}}", "{title}" in pb.template)
        check(f"  {agent_id}.dod non-vide", len(pb.dod) > 0)

# dev_app : nouveaux fichiers Round 2
dev_app_pb = get_playbook("dev_app")
if dev_app_pb:
    check("dev_app files = repo-init + mvp-sprint-1", set(dev_app_pb.files) == {
        "app/repo-init.md", "app/mvp-sprint-1-scope.md"
    })
    check("dev_app dod mentionne scaffold", any("scaffold" in d for d in dev_app_pb.dod))

check("get_playbook None pour agent inconnu", get_playbook("inexistant_agent") is None)

required = all_required_files(["spec", "pm", "marketing"])
check("all_required_files non-vide", len(required) > 0)
check(
    "direction/spec-cursor-prompt.md dans required",
    "direction/spec-cursor-prompt.md" in required,
)
check("Pas de doublons", len(required) == len(set(required)))


# ---------------------------------------------------------------------------
# 7. build_instruction_with_paths — Option A paths
# ---------------------------------------------------------------------------
print("\n[7] build_instruction_with_paths() — Option A")
instr = build_instruction_with_paths(
    agent_id="spec",
    dossier_title="Mon Projet",
    slug=SLUG,
    workspace_path=_TMP,
    context_excerpt="Résumé du dossier CEO ici.",
)
check("Instruction contient workspace path", _TMP in instr)
check("Instruction contient slug", SLUG in instr)
check("Instruction contient title", "Mon Projet" in instr)
check("Instruction contient FICHIERS À PRODUIRE", "FICHIERS À PRODUIRE" in instr)
check("Instruction contient TEMPLATE LIVRABLE", "TEMPLATE LIVRABLE" in instr)

# Option A : le path dans l'instruction doit être {ws}/direction/{slug}/spec-cursor-prompt.md
option_a_path = f"{_TMP}/direction/{SLUG}/spec-cursor-prompt.md"
check("Instruction path Option A correct", option_a_path in instr, option_a_path)

# Fallback agent inconnu
instr_fallback = build_instruction_with_paths(
    agent_id="agent_inconnu",
    dossier_title="Projet X",
    slug=SLUG,
    workspace_path=_TMP,
    context_excerpt="Contexte.",
)
check("Fallback instruction non-vide", len(instr_fallback) > 20)


# ---------------------------------------------------------------------------
# 8. _extract_text_output
# ---------------------------------------------------------------------------
print("\n[8] _extract_text_output()")

class FakeCrewAI:
    def __init__(self, raw: str):
        self.raw = raw

check("str → str", _extract_text_output("hello") == "hello")
check("dict avec content", _extract_text_output({"content": "body"}) == "body")
check("dict avec output", _extract_text_output({"output": "out"}) == "out")
check("dict avec cursor_prompt", _extract_text_output({"cursor_prompt": "spec"}) == "spec")
check("CrewAI .raw", _extract_text_output(FakeCrewAI("raw text")) == "raw text")
check("None → ''", _extract_text_output(None) == "")
check("dict vide → str(dict)", isinstance(_extract_text_output({}), str))


# ---------------------------------------------------------------------------
# Résumé
# ---------------------------------------------------------------------------
total = len(results)
passed = sum(1 for _, ok, _ in results if ok)
failed = total - passed

print(f"\n{'='*60}")
print(f"RÉSULTAT Phase 9 Option A : {passed}/{total} tests passés")
if failed:
    print(f"\nÉCHECS ({failed}) :")
    for name, ok, detail in results:
        if not ok:
            print(f"  {FAIL}  {name}" + (f" — {detail}" if detail else ""))
print(f"{'='*60}\n")

# Nettoyage temp
import shutil
try:
    shutil.rmtree(_TMP)
    print(f"Workspace temp nettoyé : {_TMP}")
except Exception:
    pass

sys.exit(0 if failed == 0 else 1)
