# SPEC — R&D Dossier Hub ALNUA

> Référence pour `.cursor/rules/rnd_dossier.mdc` et les phases d'implémentation.

## Objectif

Transformer le Centre R&D (idées auto-scorées) en **département R&D complet** :
- Dossier structuré par proposition (sections, statuts, business case)
- Comité multi-agents en langage naturel (phases 2+)
- Dossier visuel illustré + deck PDF (phases 4+)
- Pipeline social teasers → posts (phase 5+)
- Validation CEO → dispatch multi-pôles (phase 6+)
- Fiche produit / waitlist (phase 7+)

## Phases

| Phase | Scope | Statut |
|---|---|---|
| 0 | Spec + règles Cursor | done |
| 1 | Données Supabase, CRUD, promote idée→dossier, UI liste | done |
| 2 | Rédaction sections + finance + anti-fluff | done |
| 3 | Comité multi-agents | done |
| 4 | Visuels + deck PDF | done |
| 5 | Pipeline social | done |
| 6 | CEO + dispatch | done |
| 7 | Fiche produit publique + waitlist | done |
| 8 | Finitions + E2E | done |

## Tables Supabase (migration `20260613120000_rnd_dossiers.sql`)

- `rnd_ideas` — idées (remplace `data/rnd_ideas.json` progressivement)
- `rnd_dossiers` — dossier R&D par idée
- `rnd_dossier_sections` — sections avec statut
- `rnd_dossier_events` — journal d'activité
- `rnd_dossier_assets` — visuels (phase 4)
- `rnd_committee_sessions` / `rnd_committee_messages` — comité (phase 3)
- `rnd_social_calendar` — calendrier social (phase 5)
- `rnd_product_pages` — fiche produit (phase 7)

## Sections dossier (clés)

`problem` | `solution` | `market` | `mvp` | `feasibility` | `business_case` | `manufacturing` | `lore` | `visual_identity` | `social_strategy` | `risks` | `decision`

Statuts section : `draft` | `under_review` | `validated` | `needs_revision` | `skipped`

## Règles anti-fluff (phase 2+)

- Interdit : slogans sans preuve, "marché énorme", "les X vont adorer"
- Obligatoire : concurrent nommé, hypothèses pricing, exclusions MVP explicites

## API Phase 1–2

```
GET    /rnd/ideas?limit=&verdict=
GET    /rnd/ideas/{idea_id}
POST   /rnd/ideas/{idea_id}/promote          # squelette rapide (~3s) + enrich async
GET    /rnd/dossiers?status=&domain=
GET    /rnd/dossiers/{id}
GET    /rnd/dossiers/slug/{slug}
POST   /rnd/dossiers
PATCH  /rnd/dossiers/{id}
GET    /rnd/dossiers/{id}/events
POST   /rnd/dossiers/{id}/enrich
POST   /rnd/dossiers/{id}/validate-section
POST   /rnd/dossiers/{id}/request-revision
POST   /rnd/dossiers/{id}/regenerate-section
GET    /rnd/dossiers/{id}/finance
POST   /rnd/dossiers/{id}/finance/estimate
POST   /rnd/dossiers/{id}/committee/start
POST   /rnd/dossiers                              # créer depuis idée (body: idea_id)
GET    /rnd/dossiers/{id}/committee/sessions
GET    /rnd/dossiers/{id}/committee/{session_id}
POST   /rnd/dossiers/{id}/committee/{session_id}/message
POST   /rnd/dossiers/{id}/committee/{session_id}/report   # CR sans clôture
POST   /rnd/dossiers/{id}/committee/{session_id}/close
POST   /rnd/dossiers/{id}/deck/generate          # HTML + PDF (Playwright)
GET    /rnd/dossiers/{id}/deck/file?type=html|pdf
GET    /rnd/dossiers/{id}/assets
POST   /rnd/dossiers/{id}/assets/generate        # Pillow renders (hero, mockup…)
GET    /rnd/dossiers/{id}/assets/file?asset_type=hero
GET    /rnd/dossiers/{id}/social/calendar
GET    /rnd/dossiers/{id}/social/status          # unlocked après validation CEO
POST   /rnd/dossiers/{id}/social/calendar/generate   # 403 si R&D en cours
PATCH  /rnd/dossiers/{id}/social/calendar/{item_id}
POST   /rnd/dossiers/{id}/social/calendar/{item_id}/generate-post
POST   /rnd/dossiers/{id}/social/generate-all
GET    /rnd/dossiers/{id}/social/posts
GET    /rnd/dossiers/{id}/ceo/package
POST   /rnd/dossiers/{id}/ceo/generate
POST   /rnd/dossiers/{id}/ceo/decide
POST   /rnd/dossiers/{id}/ceo/dispatch
GET    /rnd/dossiers/{id}/product/status       # unlocked après CEO
GET    /rnd/dossiers/{id}/product
POST   /rnd/dossiers/{id}/product/generate     # 403 si R&D en cours
PATCH  /rnd/dossiers/{id}/product
POST   /rnd/dossiers/{id}/product/publish
POST   /rnd/dossiers/{id}/product/unpublish
GET    /rnd/product/{slug}                     # public (published=true)
GET    /rnd/health                              # santé module R&D
GET    /rnd/dossiers/{id}/pipeline              # progression phases 1–7
GET    /posts?rnd_dossier_id=
```

Page publique Next.js : `/p/{slug}` (waitlist intégrée si activée, SEO metadata).

**Phase 8 — finitions & E2E**
- `services/rnd_pipeline.py` — statut cross-phases + `/rnd/health`
- `scripts/run_rnd_tests.py` — orchestrateur suite complète
- `scripts/test_rnd_e2e.py` — parcours idea → publish sans LLM
- UI : onglet **Pipeline** dans le pitch modal (`rnd-pipeline-panel.tsx`)

**Phase 7 — fiche produit** : génération brouillon après validation CEO, publication explicite → `status=published` sur dossier. Waitlist via projet Hub lié (`ensure_project_for_dossier`).

### Env Phase 2

- `RND_COST_MODEL` — `ai_solo` (défaut) ou `human_dev` (legacy freelance)
- `RND_LLM_EUR_PER_AGENT_WEEK` — coût tokens OpenRouter par semaine pipeline
- `RND_DOSSIER_ENRICH_EUR`, `RND_PROJECT_HOSTING_MONTHLY_EUR`
- `RND_DOSSIER_USE_LLM` (default `true`) — désactiver pour tests rapides

## Fichiers locaux

```
data/rnd_dossiers/{slug}/
  dossier.md
  sections/
  deck/
    index.html
    deck.pdf
  social/
    calendar.json
  product/
    page.json
```

## Intégrations existantes

- `agents/rnd_center.py` — cycle auto + dual-write Supabase
- `services/rnd_repository.py` — CRUD
- `agents/rnd_dossier_agent.py` — promote idée → dossier
- `web/src/lib/rnd-dossier.ts` — client API
- `web/src/components/rnd/` — UI

## Règle pipeline

Ne pas commencer phase N+1 si phase N ne tourne pas.

**Phase 5 — social** : calendrier et génération de posts verrouillés tant que le dossier est en R&D (`draft`, `committee_active`, `ready_for_ceo`, etc.). Déblocage quand `status ∈ {ceo_approved, in_conception, published}` ou `ceo_status = approved`. Consultation du calendrier existant reste possible en lecture seule.

**Phase 6 — CEO + dispatch** : package CEO par branche (`app` / `gaming` / `robotics`), CR comité structuré, validation Emilie (`ceo_status`), puis dispatch COO → entrées `roadmap` + brief `agent_logs`. Migration `20260613150000_rnd_ceo_phase6.sql`.
