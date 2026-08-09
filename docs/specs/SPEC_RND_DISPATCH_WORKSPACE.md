# Spec — Phase 9 : Workspace Dispatch + Livrables Persistants

> Phase 9 du pipeline R&D ALNUA : chaque agent du dispatch CEO écrit un livrable concret sur disque,
> tracé par un manifest JSON, validé avant d'être marqué `success`.

---

## Convention disque — Option A

```
ALNUA_WORKSPACE/
  {pole}/
    {slug}/
      {livrable}.md
  {slug}.manifest.json      ← racine workspace
```

Exemple pour le projet `my-saas` :
```
C:\Dev\ALNUA\
  direction\my-saas\spec-cursor-prompt.md
  direction\my-saas\backlog-mvp.md
  direction\my-saas\acceptance-criteria-v1.md
  app\my-saas\repo-init.md
  app\my-saas\mvp-sprint-1-scope.md
  app\my-saas\scaffold\README.md
  app\my-saas\scaffold\package.json
  app\my-saas\scaffold\.gitignore
  comms\my-saas\gtm-strategy.md
  finance\my-saas\business-case.md
  my-saas.manifest.json
```

---

## Variable d'environnement

```bash
# .env (ou OS env)
ALNUA_WORKSPACE=C:\Dev\ALNUA      # Windows
ALNUA_WORKSPACE=~/Dev/ALNUA       # macOS/Linux
```

---

## API `services/rnd_workspace.py`

| Fonction | Signature | Description |
|----------|-----------|-------------|
| `init_project_workspace` | `(slug) → dict[pole, Path]` | Crée `{ws}/{pole}/{slug}/` pour chaque pôle. Idempotent. |
| `pole_path` | `(pole, slug) → Path` | `{ws}/{pole}/{slug}/` |
| `write_deliverable` | `(pole, slug, filename, content) → Path` | Écrit `{ws}/{pole}/{slug}/{filename}`. Write-only. |
| `validate_deliverables` | `(slug, ["pole/file", ...]) → dict[str, bool]` | Vérifie l'existence de chaque fichier requis. |
| `missing_deliverables` | `(slug, required) → list[str]` | Fichiers manquants. |
| `init_manifest` | `(slug, title, root, matrix)` | Crée `{ws}/{slug}.manifest.json` initial. |
| `update_manifest_agent` | `(slug, agent_id, *, status, files, error)` | Mise à jour statut agent dans le manifest. |
| `finalize_manifest` | `(slug, *, success, missing)` | Marque la validation globale. |

---

## Playbooks `services/rnd_dispatch_playbooks.py`

Chaque agent a un `AgentPlaybook` définissant :
- `pole` : pôle de destination (`direction`, `app`, `comms`, `finance`, etc.)
- `files` : fichiers requis au format `"pole/filename"`
- `template` : template markdown injecté dans l'instruction agent
- `dod` : checklist Definition of Done (validation humaine)

### Pôles couverts

| Pôle | Agents | Fichiers produits |
|------|--------|-------------------|
| `direction` | spec, pm, coo | spec-cursor-prompt.md, backlog-mvp.md, acceptance-criteria-v1.md, coo-coordination-brief.md |
| `app` | dev_app, dev_backend | repo-init.md + mvp-sprint-1-scope.md, api-brief.md |
| `gaming` | dev_gaming, game_director | dev-gaming-brief.md, gdd-extract.md |
| `comms` | marketing, content | gtm-strategy.md + content-calendar.md, messaging-brief.md |
| `finance` | accounting | business-case.md |
| `hardware` | hardware, embedded_dev | hardware-brief.md, embedded-brief.md |
| `innovation` | brainstorm, rnd_agent | ideation-brief.md, research-report.md |
| `analytics` | analyst_business, analyst_data | business-analysis.md, data-brief.md |

---

## Flux d'exécution `services/rnd_dispatch_executor.py`

```
CEO valide dossier
  → dispatch_to_coo()
      → init_project_workspace(slug)     # crée {ws}/{pole}/{slug}/ pour chaque pôle
      → init_manifest(slug, ...)
      → build_dispatch_execution_plan()
          → step 1 : COO → handle_instruction
          → step N : spec → generate_and_write_dispatch (+ ticket Supabase)
          → step N : pm  → handle_instruction (+ validation ticket+roadmap en base)
          → step N : dev_app → handle_instruction (+ scaffold généré)
          → ...
      → execute_plan()
      → pour chaque résultat :
          → _extract_text_output()
          → _write_playbook_deliverables()  # {ws}/{pole}/{slug}/{filename}
          → validate_deliverables()         # vérification existence fichier
          → agent_logs.status = success     # SEULEMENT si fichier présent
          → update_manifest_agent()
      → finalize_manifest()
      → db.update(rnd_dossiers, workspace_path, workspace_validation)  # Item 8
```

---

## Règles invariantes

- **`write_deliverable(pole, slug, filename, content)`** — args dans cet ordre
- **Write-only** : jamais de suppression ni d'écrasement sans consentement
- **`agent_logs.status=success`** uniquement après `validate_deliverables()` pour cet agent
- **`spec`** utilise `generate_and_write_dispatch` (pas `generate_from_ticket`) dans le dispatch
- **Ticket Supabase créé avant** l'appel spec, avec `workspace_slug=slug`
- **PM** vérifie ticket + roadmap en base après `handle_instruction`
- **`dev_app`** : scaffold `app/{slug}/scaffold/` créé automatiquement
- **Manifest** à `ALNUA_WORKSPACE/{slug}.manifest.json` (racine, pas dans le projet)
- **`workspace_validation`** persisté sur `rnd_dossiers` en Supabase à la fin

---

## Migration Supabase

```sql
-- supabase/migrations/20260613160000_projects_workspace_path.sql
ALTER TABLE projects
  ADD COLUMN IF NOT EXISTS workspace_path TEXT;

ALTER TABLE rnd_dossiers
  ADD COLUMN IF NOT EXISTS workspace_path TEXT,
  ADD COLUMN IF NOT EXISTS workspace_validation JSONB DEFAULT '{}'::jsonb;
```

---

## Tests

```bash
# Tests unitaires workspace (Option A paths)
python scripts/test_rnd_dispatch_workspace.py

# Test E2E avec LLM mocké
python scripts/test_rnd_dispatch_e2e_workspace.py
```

---

## UI

**`web/src/components/rnd/rnd-ceo-panel.tsx`**

Après dispatch + exécution agents, affiche :
- `workspace_path` (depuis `data.dispatch.workspace_path`)
- Bouton "Copier chemin"
- Bouton "Ouvrir dossier" → `vscode://file/{path}` (Cursor)
