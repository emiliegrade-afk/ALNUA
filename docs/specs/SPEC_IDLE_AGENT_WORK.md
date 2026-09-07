# SPEC — Idle Agent Work (travail sans brief précis)

> Contrat : ce que les agents ALNUA peuvent faire **sans demande CEO explicite**,
> tout en respectant `SPEC_WORKFLOW_ENGINE.md` (« Emilie décide le *quoi*
> stratégique ») et DEC-011 (trust) / DEC-012 (un seul moteur de recettes).
>
> **Statut :** contrat validé Emilie 2026-08-10 · **implémentation MVP :** Phase 39
> (recettes `idle_plan_day` / `idle_drain` + scheduler + gates trust/budget +
> OpenRoom runId — 2026-08-10).
> **Décision :** DEC-021.
> **Suite :** Agent Lounge (DEC-031 / Phase 46 V4) — famille idle
> `lounge_session` L0 filler — voir `docs/specs/SPEC_AGENT_LOUNGE.md` §9.
> Vocabulaire UI : OpenRoom → Lounge (présence agents conservée).
> LLM Lounge = tier fast dédié (`LOUNGE_MODEL`), pas le modèle métier.

---

## 1. Objectif

Quand le Hub tourne et qu’Emilie n’a rien demandé de précis, les agents ne restent
pas « décoratifs » : ils avancent sur **ops**, **produits** (Naïa / Wyrdheim / Eve /
Hub), **entreprise** (marque, partnerships, process) et **self-dev** (sous
conditions trust), dans des bornes de risque et de coût.

Ce n’est **pas** un second moteur : idle = recettes `workflow_engine` + jobs
APScheduler / n8n (même pattern que `run_ops` / `semaine` / `queue_academy_if_idle`).

---

## 2. Choix CEO (2026-08-10)

| Axe | Décision |
|-----|----------|
| Ambition | **C — Entreprise** : ops + tickets produit + initiatives company en L1 |
| Sélection du travail | **Hybride** : file COO auto pour L0–L1 ; L2 seulement si file du jour validée |
| Self-dev agents | **Uniquement si trust ≥ 70** (bande review / autonomous DEC-011) |
| Budget LLM idle | **Adaptatif** — pas de plafond USD figé ; voir §6 |

---

## 3. Niveaux d’action (idle)

Alignés Phase 30 `autonomy_level` + bands trust.

| Niveau | Nom | Comportement idle | Exemple |
|--------|-----|-------------------|---------|
| **L0** | Observer | Lit / indexe / résume → file CEO ou ticket | Briefing, scan erreurs, veille Explorer |
| **L1** | Préparer | Brouillon, issue, fiche — **ne publie pas**, n’exécute pas de side-effect irréversible | Draft post, PR draft, checklist safety, brief partnership |
| **L2** | Exécuter low-risk | Agit si trust OK **et** item dans file du jour **validée** | Fix bug `agent-ready`, academy lesson, sync assets déjà autorisé |
| **L3** | Stratégique | **Toujours Emilie** — jamais idle | Nouveau produit, pivot, publish public, ads spend, `budget_transfer`, dossier `ready_for_ceo`, merge `main` non gate |

**Règle hybride :**

1. Chaque matin (avec le briefing), Aria (COO) propose une **file du jour**
   (`idle_queue` : items L0–L2 classés).
2. Items **L0–L1** : exécutables dès qu’ils sont en file (pas besoin de validation
   matinale pour démarrer).
3. Items **L2** : bloqués jusqu’à validation CEO de la file (bouton / endpoint
   « Valider file du jour » sur `/ceo` ou équivalent).
4. Si pas de validation : L2 idle **ne part pas** ; L0–L1 et ops existants
   (`run_ops`, BugWatchdog, pipeline GH) continuent.

---

## 4. Allowlist par famille

Tout ce qui n’est pas listé ici est **hors idle** (demande ou ticket explicite).

### 4.1 Ops / Direction — `coo`, `qa`, `pm`, `spec`

| Autorisé idle | Max | Interdit idle |
|---------------|-----|---------------|
| `run_ops`, `semaine`, remédiation GH auto, scan erreurs | L2* | Changer priorités stratégiques produit |
| Triage backlog → issues / tickets hub | L1 | Ouvrir un chantier stratégique sans item file |
| Briefing matin + synthèse queue CEO | L0 | |

\* L2 ops déjà schedulé (BugWatchdog, `agent-ready`) reste inchangé — hors
« file du jour » mais dans le contrat Workflow Engine existant.

### 4.2 Code Hub / App — `dev_*`, `coding_coach`, `dev_backend`, …

| Autorisé idle | Max | Interdit idle |
|---------------|-----|---------------|
| Pipeline `agent-ready`, BugWatchdog | L2* | Merge `main` sans gate QA / review |
| Academy si idle + tickets labellisés | L2 (file validée) | Features hors ticket / hors file |
| Draft PR, revue locale, coach tips | L1 | |

### 4.3 Gaming — studio

| Autorisé idle | Max | Interdit idle |
|---------------|-----|---------------|
| Sync builds/assets status, GDD consistency check | L0–L1 | Ship store, lore « officielle » |
| Test-plan draft, agency run **seulement** si item file L2 validé | L2 | Spend UE lourd / agency non borné |

### 4.4 Robotique

| Autorisé idle | Max | Interdit idle |
|---------------|-----|---------------|
| BOM drift, lab status, safety checklist draft | L0–L1 | Commandes Pi destructives, hardware réel |

### 4.5 R&D

| Autorisé idle | Max | Interdit idle |
|---------------|-----|---------------|
| Veille Explorer bornée, scorer idées existantes | L0–L1 | Passer un dossier en `ready_for_ceo` |
| Enrichir un arbre **déjà ouvert** | L1 | Créer exploration sans borne / sans item file |

### 4.6 Comms — marketing, content*, ads, brand

| Autorisé idle | Max | Interdit idle |
|---------------|-----|---------------|
| Gaps calendrier, drafts Content Studio, A/B copy | L0–L1 | Publish réseaux, ads spend, campagne live |
| Initiatives marque / process en brouillon (ambition C) | L1 | |

### 4.7 Finance — `accounting`, `controller`

| Autorisé idle | Max | Interdit idle |
|---------------|-----|---------------|
| Rapport coûts, alertes budget, brouillon facture | L0–L1 | `budget_transfer`, paiements, déclarations |

### 4.8 Analytics — `analyst_*`

| Autorisé idle | Max | Interdit idle |
|---------------|-----|---------------|
| Snapshots KPIs, anomalies → ticket | L0–L1 | Décision business auto |

### 4.9 Secretary

| Autorisé idle | Max | Interdit idle |
|---------------|-----|---------------|
| Morning notify, follow-ups partnerships, SAV lite | L0–L2* | SAV sensible (contrat Workflow Engine) |

### 4.10 Self-dev (tous agents compétitifs / personas)

| Autorisé idle | Max | Condition |
|---------------|-----|-----------|
| Compress Mem0, research domaine weekly, skill synth post-tâche | L0–L1 | **trust ≥ 70** |
| — | — | trust &lt; 70 → **pas** de self-dev idle |

Interdit idle : auto-upgrade de tier, modification persona / operating spec.

### 4.11 Agent Lounge (DEC-031 / Phase 46 V4)

| Autorisé idle | Max | Condition |
|---------------|-----|-----------|
| `lounge_session` (puzzle filler) | **L0** | Budget ≠ warning/critical ; **après** items prod dans la file |
| — | — | LLM = **DeepSeek V3.2** (ou `LOUNGE_MODEL`), pas le modèle métier |

Place dans la file : **en dernier** (filler). Family `lounge` reportée si budget
`warning` (comme company / self_dev).

Cross-ref : `docs/specs/SPEC_AGENT_LOUNGE.md` §9.

---

## 5. Ambition C — initiatives entreprise

En plus des tickets produit, la file COO peut contenir des items **company** L1 :

- Brouillon process / checklist interne
- Draft partnership follow-up (pas envoi SAV sensible)
- Draft brand / content company
- Proposition d’amélioration Hub (issue `idle-ok`)

Toujours **L1** jusqu’à validation CEO pour passer en L2 (ex. ouvrir vraiment
l’issue et lancer le pipeline).

---

## 6. Budget LLM idle — adaptatif

Pas de plafond USD figé dans ce contrat. Le Hub adapte via `cost_monitor` :

| Signal `check_budget_alert` | Comportement idle |
|----------------------------|-------------------|
| `ok` | File L0–L1 normale ; L2 si file validée |
| `warning` | Idle **réduit** : prioriser ops + L0 ; reporter self-dev et company L1 |
| `critical` | Idle **stop** (sauf BugWatchdog / pipeline `agent-ready` déjà engagé) |

Paramètres (env / settings, ajustables sans nouvelle DEC) :

- `IDLE_WORK_ENABLED` (bool, défaut futur `true` quand Phase 39 livrée)
- `IDLE_DRAIN_INTERVAL_MIN` (ex. 120–240)
- `IDLE_MAX_ITEMS_PER_DRAIN` (ex. 1–3)
- Réutilise le `daily_budget_usd` déjà configuré pour les alertes — **pas** un
  second budget magique.

---

## 7. Cadence

| Moment | Action |
|--------|--------|
| Quotidien ~08:00 | Briefing + proposition **file du jour** COO |
| Après validation CEO (optionnel mais requise pour L2) | Débloquer items L2 de la file |
| Toutes les 2–4 h (`IDLE_DRAIN`) | Consommer 1–N items L0–L1 (et L2 si validés) |
| Vendredi | `semaine` + content sprint + cycle R&D (existant) |
| Continu | Ops existants (GH poll, watchdog, academy wake) |

---

## 8. Surfaces UI / API (cible Phase 39)

| Surface | Rôle |
|---------|------|
| `/ceo` | Voir / valider / éditer file du jour |
| OpenRoom / status | Statut issu de vrais `workflow_runs` / task IDs — pas load % cosmétique |
| `GET/POST /workflows/...` | Recettes `idle_plan_day`, `idle_drain` (noms indicatifs) |
| Trust UI `/trust` | Gate self-dev (≥ 70) visible |

---

## 9. Recettes à ajouter (implémentation — pas encore)

| ID (indicatif) | Head | Rôle |
|----------------|------|------|
| `idle_plan_day` | `coo` | Construire file du jour (ops + produit + company L1) |
| `idle_drain` | `coo` | Exécuter prochain item éligible selon §3 et §6 |
| (réutiliser) `run_ops`, `semaine`, validation content/campaign | — | Inchangés |

Handlers appellent services existants (`plan_executor`, academy, content drafts,
cross_dept queue drain, etc.) — **pas** de logique métier dans n8n
(`.cursor/rules/async-jobs.mdc`).

---

## 10. Hors scope V1

- Publication autonome réseaux / ads (même trust &gt; 90) — DEC-011 aspirational,
  pas idle V1
- `budget_transfer` (Phase 34 / DEC-016)
- Agency Gaming UE non bornée
- Computer-use Windows total
- Remplacer le contrat « CEO valide dossiers R&D »

---

## 11. Critères d’acceptation (quand on code)

1. Spec + DEC-021 présentes ; ROADMAP Phase 39 référencée.
2. `idle_plan_day` produit une file persistée consultable sur `/ceo`.
3. Sans validation file : aucun item L2 idle ne s’exécute ; L0–L1 oui.
4. Agent trust &lt; 70 : zéro self-dev idle (test unitaire).
5. `critical` budget : drain idle skip (test + log).
6. OpenRoom n’affiche plus un % load inventé pour le travail idle — lien run_id.

---

## 12. Liens

- `docs/specs/SPEC_WORKFLOW_ENGINE.md` — contrat autonomie CEO / Hub
- `DECISIONS.md` — DEC-011, DEC-012, **DEC-021**
- `ROADMAP.md` — Phase 39
- `services/cost_monitor.py`, `services/agent_trust.py`, `api/lifespan_*.py`
