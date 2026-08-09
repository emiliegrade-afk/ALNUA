# Architectural Decisions Log — ALNUA Hub

> Reconstitué rétroactivement le 2026-07-25 (bootstrap de gouvernance) à partir de
> l'historique Git, `CLAUDE.md` et `ruff.toml`. Une entrée acceptée ne se modifie
> jamais — si une décision change, une nouvelle entrée la remplace et marque
> l'ancienne "Superseded". À partir de maintenant, ouvrir une entrée à chaque nouvelle
> dépendance, changement de format de données, ou arbitrage structurant — ne pas
> laisser ce fichier retomber en retard comme il l'était jusqu'ici.

| ID | Sujet | Date | Statut |
|----|-------|------|--------|
| DEC-001 | Un seul montage par router, pas de préfixe `/v1` | 2026-06-13 | Active |
| DEC-002 | Tous les agents héritent de `AgentBase` | 2026-06-24 | Active |
| DEC-003 | Prompts système en "9-layer operating spec" | 2026-06-24 | Active |
| DEC-004 | Star-imports volontaires via `route_common.py` | 2026-07-23 | Active |
| DEC-005 | RLS Supabase restreinte à `SELECT` sur tables sensibles | 2026-06-12 | Active |
| DEC-006 | `X-Hub-Key` obligatoire hors développement | 2026-06-12 | Superseded (DEC-010) |
| DEC-007 | Sanitizing désactivé sur `agents_pole.py` (PII) | — | Active |
| DEC-008 | OpenHands (pipeline autonome) + Aider (fix ciblés) en parallèle | 2026-06-11 | Active |
| DEC-009 | Nwiro/UE5 coexiste avec Godot — assumé, `CLAUDE.md` corrigé | 2026-07-25 | Active |
| DEC-010 | `HUB_API_KEY` obligatoire dans tous les environnements | 2026-07-25 | Active |
| DEC-011 | Agent Trust System séparé du système de compétition | 2026-07-31 | Active |
| DEC-012 | Un seul moteur de workflow générique (extension de `workflow_engine.py`) | 2026-07-31 | Active |
| DEC-013 | Review Board générique par généralisation de `rnd_council_agent.py` | 2026-07-31 | Active |
| DEC-014 | Saisie manuelle des stats Marketing plutôt qu'intégration API Ads | 2026-08-01 | Active |
| DEC-015 | OpenRouter prompt caching + retries/timeouts anti-boucle outils | 2026-08-09 | Active |
| DEC-016 | Comptabilité : catalogue SaaS + factures sans paiement + Revolut lecture | 2026-08-09 | Active |

---

### DEC-001 — Un seul montage par router, pas de préfixe `/v1`
**Contexte :** chaque router était candidat à un double montage (racine + `/v1`) pour
préparer un futur versionnement d'API.
**Décision :** chaque router de `api/routers/ALL_ROUTERS` est monté **une seule fois**
dans `register_routers()`, sans préfixe `/v1`.
**Alternative rejetée :** montage double racine + `/v1`.
**Pourquoi rejetée :** dupliquait les `operation_id` dans le schéma OpenAPI et risquait
des collisions d'outils côté `fastapi-mcp`. Aucun consommateur (web/, n8n/, bots/)
n'utilisait `/v1`.

### DEC-002 — Tous les agents héritent de `AgentBase`
**Contexte :** chaque agent gérait `self.db`/`self.llm` à la main, dupliquant la
logique d'init et de tracing.
**Décision :** migration de 18+ agents vers `agents/agent_base.py::AgentBase`, qui
fixe `self.db`/`self.llm` dans `__init__`. Toute sous-classe qui redéfinit `__init__`
**doit** appeler `super().__init__()` en premier.
**Incident réel :** oubli corrigé sur `rnd_dossier_agent`/`rnd_committee_agent` —
`self.db` restait `None`, `self._log()` aurait levé `AttributeError` au premier appel.

### DEC-003 — Prompts système en "9-layer operating spec"
**Contexte :** le pattern initial (SYSTEM_PROMPT en 5 sections inline) devenait
difficile à maintenir cohérent entre 27 agents.
**Décision :** génération via `config/agent_operating_spec.py::get_system_prompt(agent_id)`,
un système en 9 couches plus riche. Le pattern 5-sections reste valide pour un agent
simple mais n'est plus le défaut.
**Commit :** `1a46408`.

### DEC-004 — Star-imports volontaires via `route_common.py`
**Contexte :** `ruff` signale par défaut les star-imports (F403/F405) comme un
anti-pattern.
**Décision :** ignorées volontairement dans `ruff.toml` — `from api.route_common
import *` est l'architecture voulue par tous les routers, documentée comme règle
invariante dans `CLAUDE.md`. Idem pour E402 (agents qui importent `AgentBase` avant
les imports stdlib) et E741/E401/E731 (~17 hits pré-existants, cosmétique, backlog).
**Alternative rejetée :** `__all__` explicite dans `route_common.py`.
**Pourquoi rejetée :** jugée plus fragile à maintenir que le carve-out ruff (voir
commentaire en tête de `ruff.toml`).

### DEC-005 — RLS Supabase restreinte à `SELECT` sur tables sensibles
**Décision :** les policies RLS anonymes sont restreintes en lecture seule sur les
tables sensibles.
**Commit :** `2df9669` ("fix(security): restrict anon RLS to SELECT on sensitive
tables").

### DEC-006 — `X-Hub-Key` obligatoire hors développement
**Statut :** Superseded by DEC-010 (2026-07-25) — Audit 002 a confirmé que le bypass
dev n'existe plus ; la table d'index a été alignée le 2026-08-09.
**Décision (historique) :** les routes Hub API exigent le header `X-Hub-Key` ; seule
l'exécution avec `ENVIRONMENT=development` permettait de démarrer sans clé.
**Commit :** `7c86370` ("feat(security): require X-Hub-Key on Hub API routes").
**Risque résiduel (obsolète) :** si `ENVIRONMENT` est mal positionné en prod, l'API
démarrait quand même sans clé — **fermé** par DEC-010 / SEC-002.

### DEC-007 — Sanitizing désactivé sur `agents_pole.py` (PII)
**Contexte :** `services/input_sanitizer.py::sanitize_user_input` redacte les PII par
défaut sur toutes les entrées libres destinées aux LLM.
**Décision :** désactivé spécifiquement sur les endpoints de `api/routers/agents_pole.py`.
**Pourquoi :** ces endpoints véhiculent volontairement des données business réelles —
la redaction casserait leur usage prévu.

### DEC-008 — OpenHands (pipeline autonome) + Aider (fix ciblés) en parallèle
**Contexte :** un seul outil de codage autonome (OpenHands) suffisait pour le pipeline
mais pas pour les corrections rapides et ciblées.
**Décision :** ajout d'Aider en complément, pour des fixes rapides sans passer par le
pipeline complet.
**Commit :** `0b2919d`.
**Addendum Phase D (2026-08-09) :** les modules standalone `skills/skill_openhands.py`
et `skills/skill_aider.py` (jamais branchés runtime) ont été **retirés**. Aider reste
disponible comme backend de `skills/skill_coding_agent.py` (`CODING_BACKEND=aider`).
Le chemin watchdog utilise `skills/skill_code_agent.py`. Entrypoint documenté :
`skills/coding_facade.py`.

### DEC-009 — Nwiro/UE5 coexiste avec Godot — assumé, `CLAUDE.md` corrigé
**Constat initial (2026-07-25) :** `CLAUDE.md` listait "Pas d'UE5 — aucune intégration
Unreal Engine dans aucun agent" comme règle invariante. Pourtant `skills/skill_nwiro.py`
(client MCP pour le plugin Unreal Engine 5 "Nwiro", 209 outils : Blueprints, Materials,
PIE Runtime...) existe et est référencé par `game_director_agent.py`,
`dev_gaming_agent.py` et `coo_agent.py`. En parallèle, une intégration Godot 4 existe
aussi (skill `.claude/skills/alnua-godot/`, `services/workflow_engine.py`,
`web/src/lib/console/departments.ts`).
**Décision (2026-07-25, tranchée par Emilie) :** Nwiro/UE5 est un choix assumé, adopté
après l'écriture de la règle "Pas d'UE5" — la doc était en retard sur le code, pas
l'inverse. Godot et UE5/Nwiro coexistent intentionnellement selon le projet gaming visé.
**Action :** `CLAUDE.md` corrigé (ancienne ligne "Pas d'UE5" remplacée par "UE5 via
Nwiro assumé"). Aucun changement de code — `skill_nwiro.py` et ses références restent
en l'état, ils étaient déjà conformes à l'intention réelle.

### DEC-010 — `HUB_API_KEY` obligatoire dans tous les environnements
**Contexte :** `config/settings.py` laissait l'API démarrer sans `HUB_API_KEY` tant que
`ENVIRONMENT` n'était pas `production`/`staging` (mode dev ouvert, ex-"Phase 6 DevEx" —
voir historique `tests/test_devex_phase6.py`), avec seulement un `logger.warning`. Le
Hub est déployé (Railway/Render), pas seulement exécuté en local — un déploiement qui
oublie de positionner `ENVIRONMENT=production` **et** `HUB_API_KEY` basculait toute
l'API (y compris `/mcp`, `/ide/run`, `/agents/embedded/pi-command`) en accès libre
silencieux (voir audit sécurité, `BUGS.md` SEC-002/SEC-003).
**Décision (2026-07-25, tranchée par Emilie) :** `HUB_API_KEY` devient obligatoire
inconditionnellement — `config/settings.py::_validate_security` lève une erreur au
démarrage si la clé est vide, quel que soit `ENVIRONMENT`. Plus de mode dev ouvert.
**Alternative rejetée :** durcir seulement si l'app bind sur autre chose que
`127.0.0.1` (option "nuancée" proposée mais non retenue — plus simple et plus sûr de
ne jamais avoir de bypass, y compris en local).
**Effets de bord traités :** `api/middleware.py` simplifié (suppression du bypass et du
warning devenus morts) ; `.env.example`/`README.md`/`CLAUDE.md`/`ARCHITECTURE.md` mis à
jour ; `tests/test_devex_phase6.py` réécrit pour tester le nouveau comportement (l'ancien
testait explicitement le bypass qu'on vient de supprimer). Note pour la suite : n'importe
quel script qui importe `config` (pas seulement le serveur API) exige désormais
`HUB_API_KEY` dans son environnement — `config/__init__.py` construit `settings` de
façon "eager" au premier import du package.

### DEC-011 — Agent Trust System séparé du système de compétition
**Contexte :** le brief "Command Center" d'Emilie (2026-07-31) demande un indice de
confiance par agent qui conditionne son niveau d'autonomie (< 70 % → validation manager
obligatoire, 70-90 % → Review Board, > 90 % → publication autonome sur tâches à faible
risque). `services/competition.py` existe déjà (`POINT_VALUES`, `add_points`,
`get_leaderboard`) mais est un score **cumulatif** de gamification (paliers à
100/200/500, ne redescend jamais).
**Décision :** le Trust Score est un nouveau service dédié (`services/agent_trust.py`,
Phase 31 de `ROADMAP.md`), avec sa propre table — **pas** une extension de
`services/competition.py`.
**Alternative rejetée :** ajouter un champ `trust` calculé à partir des points de
compétition existants.
**Pourquoi rejetée :** les deux métriques mesurent des choses différentes — la
compétition récompense le volume/l'engagement (motivation), le trust doit mesurer la
fiabilité récente (gouvernance) et donc pouvoir **décroître**. Un agent qui empile des
points de complaisance deviendrait "de confiance" à tort si les deux étaient fusionnés.

### DEC-012 — Un seul moteur de workflow générique
**Contexte :** le brief Emilie demande des "workflows de validation" configurables
(niveaux d'autonomie 0-3, ex. Content→Brand→Marketing→CEO→Publication). Un moteur de
recettes/étapes existe déjà : `services/workflow_engine.py` (statuts
`PENDING/IN_PROGRESS/OK/A_VERIFIER/ECART`, blocage sur écart), utilisé aujourd'hui pour
les recettes ops/ship/watchdog (`api/routers/workflows.py`).
**Décision :** étendre `services/workflow_engine.py` avec de nouvelles recettes
(`content_validation`, `campaign_validation`, `budget_transfer` — Phase 30 de
`ROADMAP.md`) plutôt que d'écrire un second moteur dédié aux validations métier.
**Alternative rejetée :** un moteur de workflow séparé, spécifique aux validations
Marketing/Finance/Brand.
**Pourquoi rejetée :** `workflow_engine.py` a déjà exactement le modèle nécessaire
(étapes séquentielles, statuts, blocage) ; dupliquer l'infrastructure pour un scope
fonctionnel différent aurait été une duplication pure, pas une différence réelle de
besoin.

### DEC-013 — Review Board générique par généralisation de `rnd_council_agent.py`
**Contexte :** le brief Emilie demande un "Review Board" transversal qui ne produit pas
de contenu mais juge (scores par axe + verdict). `agents/rnd_council_agent.py` fait déjà
exactement cela pour le Comité R&D — 5 personas, verdict `GO/MAYBE/NO`, `confidence_pct`,
`axis_scores` JSONB (table `rnd_committee_votes`).
**Décision :** généraliser ce pattern (Phase 32 de `ROADMAP.md`) — reviewers et critères
configurables par recipe (ex. Anouk=brand, Léo=SEO/conversion, Camille=cohérence pour
Marketing), plutôt que créer un nouvel agent de comité par département.
**Alternative rejetée :** un agent "Review Board" dédié par département (ex.
`marketing_review_board_agent.py`, `finance_review_board_agent.py`), sur le modèle de
`rnd_council_agent.py` dupliqué.
**Pourquoi rejetée :** la logique de vote/agrégation (démarrage session, délibération
parallèle par persona, calcul de jauges, clôture) est identique quel que soit le
département — seuls les reviewers et les critères changent. Dupliquer l'agent aurait
recréé le problème que DEC-002 (`AgentBase`) avait déjà résolu pour l'init agent.

### DEC-014 — Saisie manuelle des stats Marketing plutôt qu'intégration API Ads
**Contexte :** la Vue Globale Marketing (Phase 29/33) excluait Performances par canal,
Top contenus (reach%) et Entonnoir de conversion faute de source de donnée — traité comme
une fin de non-recevoir plutôt qu'un backlog. Emilie a demandé explicitement de créer les
champs/flux manquants (Phase 37 de `ROADMAP.md`).
**Décision :** ajouter des colonnes de stats nullable sur `campaigns`/`posts_queue` et une
table `funnel_snapshots`, remplies par saisie manuelle (Emilie/Léo/Camille copient les
chiffres depuis les dashboards natifs Meta/TikTok/Google Ads, App Store Connect, Plausible,
etc.) via `CampaignModal`/`PostEditModal`/`FunnelEntryModal`. Tous ces champs restent `NULL`
tant que personne n'a saisi de vraie valeur — jamais un 0 ou une estimation par défaut.
**Alternative rejetée :** intégration API temps réel avec Meta Ads/TikTok Ads/Google
Ads/LinkedIn Ads pour un pull automatique de reach/engagement/ROI.
**Pourquoi rejetée (pour l'instant) :** chaque plateforme exige une app OAuth dédiée, une
vérification business, la gestion de quotas/rate limits, et l'obtention d'un accès aux
comptes ad réels — un chantier de plusieurs semaines par plateforme, disproportionné tant
qu'on ne sait pas si la donnée manuelle suffit à l'usage réel. Reste une évolution
possible, non exclue, si la saisie manuelle s'avère trop lourde.

### DEC-015 — OpenRouter prompt caching + retries/timeouts anti-boucle outils
**Contexte :** les agents CrewAI re-envoient à chaque itération des schémas d'outils
(Composio/MCP/Hub tools) quasi-statiques ; sans prompt caching OpenRouter, l'input lourd
est refacturé plein tarif. Les timeouts 120 s × 3 retries × fallback modèle + boucles
`skill_retry_loop` sur erreurs MCP/auth brûlaient des tokens inutiles.
**Décision :**
1. `services/openrouter_prompt_cache.py` — `session_id` sticky par agent +
   `cache_control` top-level (TTL 1h) + breakpoints explicites sur SYSTEM pour
   Anthropic/Gemini/Qwen ; contexte compétitif dynamique hors du préfixe caché.
2. `LLMClient` / CrewAI `additional_params` / `rnd_center` branchés dessus.
3. Timeouts HTTP 60 s (défaut), max 2 tentatives/modèle, pas de failover sur timeout ;
   `skill_retry_loop` : 1 seule tentative sur MCP/Composio/tool-schema/auth ;
   `max_iter` CrewAI plafonné via `config/llm_runtime.py` (6 défaut, 8 COO).
**Alternative rejetée :** laisser le caching « automatique » sans `session_id` ni
séparation static/dynamic, et garder 3 retries + failover timeout.
**Pourquoi rejetée :** sans sticky session le cache DeepSeek/MiniMax rate souvent ;
failover timeout double la facture sans augmenter le taux de succès outil.

### DEC-016 — Comptabilité : catalogue SaaS + factures sans paiement + Revolut lecture
**Contexte :** Emilie veut que Jules/Rémi voient tous les abonnements (catalogue),
les coûts live (OpenRouter), gèrent les factures sans pouvoir payer, et lient
Revolut si possible. Nadia doit utiliser `alnua.global@gmail.com`.
**Décision :**
1. `data/saas_subscriptions.json` + `services/saas_spend.py` — catalogue injecté
   dans Jules/Rémi ; agrégat live OpenRouter + manuel + estimés + Revolut.
2. `services/finance_invoices.py` — ledger factures (draft→to_pay→paid_externally) ;
   **aucun paiement automatisé** — Emilie paie hors Hub.
3. `services/revolut_business.py` — GET `/expenses` si `REVOLUT_ACCESS_TOKEN`
   (Business Grow+) ; sinon statut explicite « non configuré ».
4. Endpoints : `GET /finances/saas-spend`, `/finances/invoices`, `/finances/revolut/status` ;
   `GET /assistant/connections` expose `gmail.ok` / profile.
**Alternative rejetée :** laisser Jules inventer les montants SaaS, ou brancher un
paiement Revolut auto depuis les agents.
**Pourquoi rejetée :** inventer des coûts fausse la compta ; paiement auto = risque
sécurité / conformité inacceptable pour une solopreneuse.
