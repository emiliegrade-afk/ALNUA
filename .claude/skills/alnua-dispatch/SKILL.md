# /alnua-dispatch — Workspace Dispatch Phase 9

Skill Cursor pour travailler sur le système de dispatch R&D avec livrables persistants sur disque.

## Architecture Phase 9

```
CEO approve dossier
    → dispatch_to_coo()
        → init_project_workspace(slug)          # crée C:\Dev\ALNUA\{slug}\{pole}\
        → init_manifest(slug, title, matrix)    # {slug}.manifest.json
        → build_dispatch_execution_plan()       # steps avec instructions enrichies
        → execute_plan()                        # agents travaillent
        → _write_playbook_deliverables()        # écriture disque par agent
        → validate_deliverables()               # tous les fichiers requis existent ?
        → finalize_manifest()                   # manifest final
```

## Fichiers clés

| Fichier | Rôle |
|---------|------|
| `services/rnd_workspace.py` | Foundation : init, write, validate, manifest |
| `services/rnd_dispatch_playbooks.py` | Playbook par agent : pole, files, template, DoD |
| `services/rnd_dispatch_executor.py` | Orchestrateur principal (refactorisé Phase 9) |
| `agents/rnd_ceo_agent.py` | `dispatch_to_coo()` → appelle init_project_workspace |
| `agents/spec_agent.py` | `generate_and_write_dispatch()` → écrit spec-cursor-prompt.md |
| `config/paths.py` | `get_alnua_workspace()` → résout ALNUA_WORKSPACE |
| `config/settings.py` | `alnua_workspace: str` — champ Settings |

## Structure workspace

```
C:\Dev\ALNUA\
  {slug}/
    {slug}.manifest.json
    direction/
      spec-cursor-prompt.md       ← Spec (Léon Marchand)
      backlog-mvp.md              ← PM (Sam Rivera)
      acceptance-criteria-v1.md  ← PM
      coo-coordination-brief.md  ← COO (Aria Voss)
    app/
      tech-brief.md               ← dev_app (Théo Laurent)
      api-brief.md                ← dev_backend (Hao Chen)
    gaming/
      gdd-extract.md              ← game_director (Mira Chen)
      dev-gaming-brief.md         ← dev_gaming (Nova Fischer)
    comms/
      gtm-strategy.md            ← marketing (Camille Rousseau)
      content-calendar.md        ← marketing
      messaging-brief.md         ← content (Sofia Reyes)
    finance/
      business-case.md           ← accounting (Jules Bernard)
    hardware/
      hardware-brief.md          ← hardware (Yuki Tanaka)
      embedded-brief.md          ← embedded_dev (Zara Singh)
    innovation/
      ideation-brief.md          ← brainstorm (Idris Okonkwo)
      research-report.md         ← rnd_agent (Alex Mercer)
    analytics/
      business-analysis.md       ← analyst_business (Layla Hassan)
      data-brief.md              ← analyst_data (Axel Roux)
```

## Règles invariantes Phase 9

- **Ne jamais supprimer** de fichiers dans ALNUA_WORKSPACE — write-only
- **Ne jamais marquer dispatch success** sans validate_deliverables() passé
- **Ne jamais tronquer** l'output agent à 1500 chars — stocker complet (4000 max Supabase)
- **Toujours** créer le workspace avant le dispatch : init_project_workspace(slug) en premier

## API workspace

```python
from services.rnd_workspace import (
    init_project_workspace,   # init_project_workspace(slug) → Path
    write_deliverable,        # write_deliverable(slug, pole, filename, content) → Path
    validate_deliverables,    # validate_deliverables(slug, ["direction/spec.md"]) → dict
    missing_deliverables,     # missing_deliverables(slug, required) → list[str]
    read_manifest, update_manifest_agent, finalize_manifest,
)
```

## Débugger un dispatch sans fichiers

```bash
cat C:\Dev\ALNUA\{slug}\{slug}.manifest.json | python -m json.tool
python scripts/test_rnd_dispatch_workspace.py
grep ALNUA_WORKSPACE .env
```
