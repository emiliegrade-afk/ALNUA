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
| DEC-009 | Nwiro/UE5 coexiste avec Godot — assumé, `CLAUDE.md` corrigé | 2026-07-25 | Superseded (DEC-017) |
| DEC-010 | `HUB_API_KEY` obligatoire dans tous les environnements | 2026-07-25 | Active |
| DEC-011 | Agent Trust System séparé du système de compétition | 2026-07-31 | Active |
| DEC-012 | Un seul moteur de workflow générique (extension de `workflow_engine.py`) | 2026-07-31 | Active |
| DEC-013 | Review Board générique par généralisation de `rnd_council_agent.py` | 2026-07-31 | Active |
| DEC-014 | Saisie manuelle des stats Marketing plutôt qu'intégration API Ads | 2026-08-01 | Active |
| DEC-015 | OpenRouter prompt caching + retries/timeouts anti-boucle outils | 2026-08-09 | Active |
| DEC-016 | Comptabilité : catalogue SaaS + factures sans paiement + Revolut lecture | 2026-08-09 | Active |
| DEC-017 | Pont Gaming = serveur UE5.8 (chat + GDD + outils agents) ; Nwiro abandonné | 2026-08-09 | Active |
| DEC-018 | Eve Pi différé ; agents via Hub SSH (`PI_HOST`) ; WinSCP = humain seulement | 2026-08-09 | Active |
| DEC-019 | UI Finance/Marketing = `*-v2` live ; stash pole-dashboard BUG-019 jeté | 2026-08-09 | Active |
| DEC-020 | Agency Gaming PC = Claude Code sur `UE_PROJECT_PATH` (+ outils UE5.8) | 2026-08-10 | Active |
| DEC-021 | Idle agent work — ambition entreprise, file hybride, trust, budget adaptatif | 2026-08-10 | Active |
| DEC-022 | Agent isolation — resource locks + slots + integrator-only merge (AAF Phase A) | 2026-08-10 | Active |
| DEC-023 | Mission Graph — façade plan_executor, pas de 3ᵉ moteur (AAF Phase B) | 2026-08-10 | Active |
| DEC-024 | Loop Engine — FSM execute/evaluate/feedback/retry (AAF Phase C) | 2026-08-10 | Active |
| DEC-025 | Review Chain — AUTO→BOARD→POLICY→INTEGRATE + merge autonomy (AAF Phase D) | 2026-08-10 | Active |
| DEC-026 | Capability Packs + PermissionGuard + Trust Graph (AAF Phase E) | 2026-08-10 | Active |
| DEC-027 | Context Engine L1–L4 + collective promotion (AAF Phase F) | 2026-08-10 | Active |
| DEC-028 | Clés Hub scopées + allowlist IP optionnelle (H2 sécurité) | 2026-08-11 | Active |
| DEC-029 | Security Sentinel (Hugo) — patrouille Hub ≠ Sentry | 2026-08-11 | Active |
| DEC-030 | PC housekeeper — quarantaine avant delete + autonomie progressive | 2026-08-11 | Active |
| DEC-031 | Agent Lounge remplace OpenRoom ; scores séparés | 2026-08-11 | Active |
| DEC-032 | Critères « Hub 100 % logiciel » + phases 31/32/34 closes | 2026-08-12 | Active |
| DEC-033 | Overlay Jarvis — faits texte / réplique voix ; Edge TTS v1 | 2026-08-14 | Active |
| DEC-034 | Gaming Academy paper slice | 2026-09-08 | Active |
| DEC-035 | Génération 3D Meshy Phase 48.4 | 2026-09-08 | Active |
| DEC-036 | Studio Academies par département | 2026-09-08 | Active |
| DEC-037 | Modèles LLM selon l'utilité métier | 2026-09-09 | Active |
| DEC-038 | Jarvis Live — voix temps réel + tâches asynchrones | 2026-10-04 | Active |
| DEC-039 | Nadia Live — actions PC en liste blanche | 2026-10-04 | Active (Lot 5 implémenté 2026-10-06) |
| DEC-040 | Bibliothèque fichiers utilisateur Hub (`/hub/files`) | 2026-10-10 | Active |
| DEC-041 | Spark / Desk figé ; Hub s'ouvre sur Command Center | 2026-10-10 | Active |
| DEC-044 | Nadia Live — écran + clic/frappe confirmés | 2026-10-10 | Active |

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
Le chemin watchdog utilise `skills/skill_code_agent.py`.
**Addendum Vague 4 (2026-08-09) :** `skills/coding_facade.py` (wrapper non appelé)
retiré — appeler directement `skill_coding_agent` / `skill_code_agent`.

### DEC-009 — Nwiro/UE5 coexiste avec Godot — assumé, `CLAUDE.md` corrigé
**Statut :** Superseded by DEC-017 (2026-08-09) — Nwiro abandonné au profit d’un
serveur UE5.8 ; Godot reste optionnel en parallèle.
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
**Action (historique) :** `CLAUDE.md` corrigé (ancienne ligne "Pas d'UE5" remplacée par
"UE5 via Nwiro assumé").

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
**Note P0 (2026-08-09) :** le workflow `budget_transfer` (Phase 30/34) reste
**explicitement reporté** — pas de stub, pas de paiement/transfert auto entre
départements. Les enveloppes budgets manuelles (ledger JSON Vague 3) suffisent
jusqu’à besoin métier réel.
**Note DEC-032 (2026-08-12) :** Phase 34 close **sans** `budget_transfer` ;
hors tampon « Hub 100 % logiciel ».

### DEC-017 — Pont Gaming = serveur UE5.8 ; Nwiro abandonné
**Contexte :** Emilie abandonne le plugin Nwiro comme pont agents↔éditeur. Besoin
produit : un **serveur UE5.8** joignable par le Hub / Claude / LLM — chat studio,
sync GDD, outils d’autonomie pour les agents Gaming (pas seulement un probe MCP
éditeur).
**Décision :**
1. **Cible** : serveur UE5.8 (HTTP/WebSocket ou protocole dédié) exposant au
   minimum : santé/connexion, chat agents, lecture/écriture GDD contrôlée, outils
   d’édition/autonomie pour `ai_programmer` / `technical_artist` / `vfx_artist` /
   `dev_gaming` (étendue Phase 21).
2. **Nwiro** : **abandonné** comme direction d’intégration. `skills/skill_nwiro.py`
   et les probes `nwiro-probe` restent en place jusqu’au skill de remplacement
   (`skill_ue58` ou équivalent) — pas de suppression big-bang ; nouveaux
   développements Gaming ne doivent **pas** dépendre de Nwiro.
3. **Godot** : reste utilisable en parallèle (projets Godot / godot-mcp) — pas
   exclusif avec UE5.8.
4. Remplace DEC-009 pour la partie « pont UE5 = Nwiro ».
**Alternative rejetée :** continuer à investir dans Nwiro MCP (209 tools) comme
chemin principal.
**Pourquoi rejetée :** Emilie veut un serveur contrôlé (chat + GDD + autonomie),
pas un plugin éditeur tiers comme contrat durable Hub↔studio.
**Suite :** Vague A Phase 21 — spec courte API + skill Hub + bascule probes.

### DEC-018 — Eve Pi différé ; agents via Hub SSH
**Contexte :** le robot Eve n’a pas encore de Raspberry Pi joignable en permanence ;
les probes `firmware` / `embedded` existent déjà. Emilie préfère que les **agents**
passent par le Hub (SSH) plutôt que WinSCP.
**Décision :**
1. **Pi optionnel** jusqu’à `PI_HOST` (+ `PI_USER` / clé) configuré — les endpoints
   renvoient un statut honnête (`PI_NOT_CONFIGURED` / probe fail), jamais de fake
   télémétrie.
2. Quand le Pi est là : commandes agents uniquement via `skills/skill_pi_ssh.py`
   (denylist, trust boundary documentée — SEC-003).
3. **WinSCP** (ou équivalent) : transfert de fichiers **humain** seulement — pas
   un chemin d’exécution pour les agents.
4. App compagnon Eve = `dev_app` (pattern Naïa) ; hardware physique =
   electronics / mechanical / firmware / embedded (déjà clarifié côté BOM IA).
**Alternative rejetée :** exiger le Pi avant tout skill robotique Phase 21.
**Pourquoi rejetée :** BOM / montage / alternatives IA sont déjà utiles sans Pi.

### DEC-019 — UI Finance/Marketing = `*-v2` ; stash BUG-019 jeté
**Contexte :** Vague 0 avait stashé un WIP « pole-dashboard » sur `/finances` /
`/marketing` (BUG-019) pour ne pas régresser les ré-exports live vers `*-v2`.
**Décision :** les routes primaires restent les shells `finances-v2` /
`marketing-v2`. Le stash `WIP BUG-019 pole-dashboard…` est **jeté** — pas de
reprise de ce draft sans nouvelle DEC + plan de remplacement explicite.
**Alternative rejetée :** `git stash pop` et fusionner pole-dashboard maintenant.
**Pourquoi rejetée :** `*-v2` est la UI live validée ; réintroduire le draft
sans DEC recrée le risque BUG-019.

### DEC-020 — Agency Gaming PC = Claude Code sur le projet UE
**Contexte :** Emilie veut que les agents Gaming (Nova, Kenji, Otto, Diego…)
puissent **agir sur son PC** comme Claude Code / Cowork pour travailler dans
UE5.8 — pas seulement bavarder via HTTP.
**Décision :**
1. **Code sur le PC** : `skills/skill_gaming_agency.py` lance le même pipeline
   que l’Academy (`skill_coding_agent` / Claude Code CLI ou `CODING_BACKEND=hub`)
   dans un **worktree git isolé** de `UE_PROJECT_PATH` (alias `REPO_PATH_GAMING`).
   Endpoints : `GET /gaming/studio/agency/status`, `POST /gaming/studio/agency/run`.
2. **Éditeur Unreal** : actions PIE/Blueprint/Niagara via
   `POST /gaming/ue58/tools/call` quand le serveur UE5.8 est up (DEC-017).
3. **Agents autorisés** : roster studio (`dev_gaming`, `ai_programmer`,
   `technical_artist`, `vfx_artist`, …) ; ajoutés à `CODING_AGENT_IDS` pour
   Kenji/Otto/Diego.
4. **Hors scope** : contrôle GUI Windows total (souris, fenêtres) type computer-use
   Anthropic — trop large / trop risqué ; réouvrir une DEC si besoin.
**Alternative rejetée :** élargir `/ide/run` ou donner un shell Windows non jailed.
**Pourquoi rejetée :** SEC-001 / allowlist IDE existent pour une raison ; l’agency
Gaming réutilise le modèle worktree déjà éprouvé.

### DEC-021 — Idle agent work (travail sans brief CEO précis)
**Contexte :** audit branchement 2026-08-10 — les agents sont surtout
request-driven ; l’ops autonome existe (`run_ops`, BugWatchdog, academy) mais pas
de contrat pour avancer produits / entreprise / self-dev sans demande. Emilie
veut que le siège « travaille vraiment » hors brief ponctuel, sans abandonner le
contrôle stratégique (`SPEC_WORKFLOW_ENGINE.md`).
**Décision (choix CEO 2026-08-10) :**
1. **Ambition C — Entreprise** : idle couvre ops + tickets produit + initiatives
   company en L1 (brouillons / issues), pas seulement academy/ops.
2. **Sélection hybride** : Aria propose une file du jour ; L0–L1 s’exécutent dès
   qu’ils sont en file ; L2 seulement après validation CEO de cette file.
3. **Self-dev** (Mem0 compress, research domaine, skill synth) : uniquement si
   trust ≥ 70 (DEC-011) — pas de self-dev idle sous ce seuil.
4. **Budget LLM idle adaptatif** : pas de plafond USD figé ; throttle via
   `cost_monitor.check_budget_alert` (`ok` / `warning` / `critical`).
5. **Implémentation** : étendre `workflow_engine` (DEC-012) + scheduler/n8n —
   pas un second moteur ; contrat dans `docs/specs/SPEC_IDLE_AGENT_WORK.md` ;
   livraison = Phase 39 ROADMAP.
**Alternatives rejetées :**
- Ambition A/B seule (trop étroit vs objectif « entreprise vivante »).
- File 100 % auto L2 sans validation matinale (risque side-effects).
- Self-dev pour tous sans trust (pollution mémoire / coût).
- Plafond USD hardcodé dans la DEC (trop rigide ; settings + alertes suffisent).
**Pourquoi :** hybride + trust + budget adaptatif garde le « 100 % autonome sauf
le quoi stratégique » tout en élargissant le terrain de jeu idle.

### DEC-022 — Agent isolation (locks + slots + merge integrator)
**Contexte :** intégration des patterns AAF manquants — sans isolation, le
parallélisme (`parallel_runner`, plans COO, coding worktrees, idle) risque
d’overwrite silencieux (même fichier / ticket / dossier) et de merges `main`
par des exécuteurs. Spec : `docs/specs/SPEC_AGENT_ISOLATION.md`.
**Décision :**
1. **Resource locks** (`services/resource_locks.py`) — fail-closed, TTL, wait
   puis deny ; clés `ticket:` / `path:` / `dossier:` / `campaign:` / `task:` /
   `data:`.
2. **Execution slots** (`services/execution_slots.py`) — plafonds global /
   per-repo / per-agent (settings `ISOLATION_MAX_*`).
3. **Merge policy** (`services/merge_policy.py`) — branches protégées
   `main`/`master`/`staging` : `dev_integrator` ; `fix_pipeline` (hotfix
   opt-in) ; academy auto-merge ; `coding_pipeline` → staging seulement si
   `CODING_AUTO_MERGE`.
4. Câblage : coding backends, `parallel_runner`, `plan_executor`,
   `fix_pipeline` ; API `GET /isolation/*`.
**Alternatives rejetées :**
- Verrou exclusif sur tout le repo (tuerait le parallèle worktree légitime).
- Faire confiance au LLM / prompts pour « ne pas toucher aux fichiers des autres ».
- Second moteur d’orchestration (DEC-012 inchangé).
**Pourquoi :** lois déterministes hors LLM — même esprit AAF PermissionGuard /
Worktree, sans réécrire le Kernel.

### DEC-023 — Mission Graph (façade plan_executor)
**Contexte :** AAF Phase B — besoin d’un graphe Mission→Tasks (`depends_on`)
unique pour parallèle/séquentiel, visible OpenRoom/CEO, sans créer un 3ᵉ moteur
à côté de `workflow_engine` (DEC-012) et `plan_executor`.
**Décision :**
1. Agrégat `Mission` + `MissionTask` persisté dans `data/missions/{id}.json`.
2. Dispatch = même `_execute_step` / isolation Phase A que `plan_executor`.
3. `run_coo_plan` persiste et exécute via Mission Graph.
4. API `/missions*` + overlay OpenRoom (`missionId`).
5. Spec : `docs/specs/SPEC_MISSION_GRAPH.md`.
**Alternatives rejetées :** second moteur DAG ; stocker seulement dans
`workflow_runs` (mauvais modèle recettes vs missions multi-agents).
**Pourquoi :** unifie la vue sans dupliquer l’exécution.

### DEC-024 — Loop Engine (execute → evaluate → feedback → retry)
**Contexte :** AAF Phase C — le loop vérif/correction n’existait vraiment que
dans `fix_pipeline` ; Mission Graph / plan_executor retentaient sans feedback
structuré ; `workflow_engine` ne connaissait que `ECART` (humain).
**Décision :**
1. Service `services/loop_engine.py` — FSM PENDING→EXECUTING→EVALUATING→
   COMPLETED | FAILED | ESCALATED ; rejet sans feedback interdit.
2. `fix_pipeline` et `plan_executor._execute_step` passent par ce moteur.
3. `workflow_engine` : statut `RETRYABLE` (rejoue l’étape avec
   `ctx[_step_feedback]`) vs `ECART` (blocage humain).
4. Caps `LOOP_MAX_ITERATIONS` / `LOOP_STRICT_MAX_ITERATIONS` (settings) ;
   `is_strict_loop` + `resolve_max_iterations` branchés sur merge / ship /
   integrator / fix_pipeline.
5. Spec : `docs/specs/SPEC_LOOP_ENGINE.md`.
**Alternatives rejetées :** dupliquer le while de fix_pipeline partout ;
fusionner Loop et Mission Graph en un seul monolithe.
**Pourquoi :** un contrat unique de self-correction, borné, avec feedback brut.

### DEC-025 — Review Chain + merge autonomy
**Contexte :** AAF Phase D — gates et merge n’étaient pas le même contrat
partout (coding, fix_pipeline, ship, Mission).
**Décision :**
1. Service `services/review_chain.py` — ordre fixe AUTO → BOARD → POLICY →
   INTEGRATE? → DONE ; auto avant humain.
2. `merge_autonomy()` : academy auto ; staging si trust ≥ seuil ; main jamais
   auto idle ; ads/finances/publish → humain ; hotfix `fix_pipeline` excepté.
3. N>1 feature branches → INTEGRATE (`dev_integrator`) obligatoire.
4. Recette workflow `mission_ship` ; API `/review-chain/*`.
5. Spec : `docs/specs/SPEC_REVIEW_CHAIN.md`.
**Alternatives rejetées :** dupliquer QA/Spec dans chaque pipeline ; auto-merge
`main` Hub « pour coller à AAF ».
**Pourquoi :** un seul chemin de ship, fail-fast, sans toucher main sans humain.

### DEC-026 — Capability Packs + PermissionGuard + Trust Graph
**Contexte :** AAF Phase E — le LLM peut « vouloir » un tool ; rien de
mathématique ne l’arrêtait partout (merge, ads, etc.).
**Décision :**
1. Catalogue `config/capability_catalog.py` + packs
   `config/capability_packs.py` (Capability ≠ Skill).
2. `services/permission_guard.py` — fail-closed ; inconnu = deny ;
   `PERMISSION_GUARD_ENABLED` pour compat.
3. Trust Graph append-only `data/trust_graph.jsonl` (≠ Trust Score DEC-011).
4. Câblé sur merge / ads / worktree / mail / git / PR / abort ; API
   `/capabilities*`, `/permission-guard/check`, `/trust-graph/recent`.
5. MCP progressif : `X-MCP-Agent` + `config/mcp_capability_routes.py` +
   middleware ; `PERMISSION_GUARD_MCP_ENABLED` ; packs `cursor`/`mcp_client`.
6. Spec : `docs/specs/SPEC_CAPABILITY_GUARD.md`.
**Alternatives rejetées :** laisser merge_policy seul (pas de catalogue
   explicite) ; Trust Score comme journal (mauvais modèle) ; Neo4j obligatoire.
**Pourquoi :** deny déterministe avant side-effect, auditable.

### DEC-027 — Context Engine L1–L4 + Collective Intelligence
**Contexte :** AAF Phase F — leçons Mem0 et library existaient, mais pas de
couches stratifiées ni wipe working memory, ni promotion bureau.
**Décision :**
1. `services/context_engine.py` compile L1 policies → L2 standards/library/
   collective → L3 Mem0 → L4 working.
2. L4 dans `data/working_memory/` ; wipe obligatoire en fin de step plan.
3. Promotion : ≥N agents même room, même fingerprint → Mem0 `bureau:{room}`
   + `collective_lessons.json`.
4. `inject_learning_context` délègue au moteur ; API `/context/*`.
5. Spec : `docs/specs/SPEC_CONTEXT_ENGINE.md`.
**Alternatives rejetées :** Neo4j obligatoire ; 2ᵉ store vectoriel parallèle.
**Pourquoi :** prompts stables + pas de contamination L4 entre missions.

### DEC-028 — Clés Hub scopées + allowlist IP optionnelle
**Contexte :** une seule `HUB_API_KEY` ouvrait Next, n8n, Cursor MCP et scripts
avec le même secret — fuite d’un canal = accès total. Objectif H2 « béton armé »
pour cockpit privé / futur VPS VPN, sans SSO multi-user.
**Décision (2026-08-11) :**
1. Master `HUB_API_KEY` reste obligatoire (DEC-010).
2. Clés canal optionnelles acceptées en parallèle : `HUB_API_KEY_WEB`,
   `_N8N`, `_MCP`, `_CURSOR` (`services/hub_auth.py`).
3. `HUB_IP_ALLOWLIST` optionnelle (IPs exactes, virgule) — vide = désactivé.
4. Coding agent shell aligné SEC-001 (metachars + premier token exact).
5. Webhook secrétaire exempté Hub-Key comme le COO ; secrets webhook toujours
   requis en prod (inchangé).
6. Checklist VPS : `docs/guides/SECURITY_HARDENING.md`.
**Alternatives rejetées :** OAuth SSO ; rotation auto 30j ; WAF public.
**Pourquoi :** réduit le blast radius par canal, reste mono-opérateur.

### DEC-029 — Security Sentinel (Hugo) distinct de Sentry
**Contexte :** Sentry couvre les crashs apps ; besoin d’une patrouille Hub
(intrusion / fuite / clé faible) avec prévention locale.
**Décision (2026-08-11) :**
1. Agent `security_sentinel` + `services/security_sentinel.py` — findings sur
   clé courte, allowlist manquante en prod, `.env` tracké Git, rafales d’auth.
2. Middleware enregistre les 401/403 ; lockdown → localhost only via
   `client_ip_allowed` ; auto-lockdown seulement si `SECURITY_AUTO_LOCKDOWN=1`.
3. Cron 30 min + endpoints `/ops/security/*` ; notify Hub sur high/critical.
**Alternatives rejetées :** fusionner avec Sentry ; WAF cloud obligatoire.
**Pourquoi :** prévention Hub mono-user sans confondre monitoring crash produit.

### DEC-030 — PC housekeeper : quarantaine avant delete
**Contexte :** Emilie veut qu’un agent range le PC (Desktop/Documents/Downloads)
avec un vrai accès fichiers, sans risque de suppressions silencieuses.
**Décision (2026-08-11) :**
1. Agent `housekeeper` (Clara Nest) + `services/pc_housekeeper*` — scan →
   propose → apply (moves) ; delete uniquement via **quarantaine** puis
   `purge_quarantine(confirm=True)`.
2. Rapport JSON de chaque apply/quarantine dans `data/housekeeper_reports/`.
3. Racines : Desktop/Documents/Downloads + `HOUSEKEEPER_ROOTS` (`;`-séparé).
4. Chemins système bloqués (`.git`, `AppData`, etc.). Autonomie (`set_autonomy`)
   après confiance (bons rapports) — jamais de delete auto sans confirm.
5. Nadia NL `housekeep` + API `/housekeeper/*` ; UI secrétariat.
**Alternatives rejetées :** delete direct ; agent avec shell libre.
**Pourquoi :** rangement utile + filet de sécurité CEO-friendly.

### DEC-031 — Agent Lounge remplace OpenRoom ; scores séparés
**Contexte :** besoin d’un espace expérimental / gamifié pour les agents (changement
de contexte, challenges, collab), sans confondre avec la compétition métier ni le
trust. OpenRoom était devenu « salle de repas & détente » — trop faible comme
couche Agentic OS. Brief Emilie 2026-08-11 + maquette Agent Lounge.
**Décision (2026-08-11) :**
1. **OpenRoom / repas disparaît** — remplacé par **Agent Lounge** (`/lounge` ;
   redirect `/openroom` ; hotspot HQ + SiegeLifeLinks).
2. **Deux classements indépendants** : `competition.py` (prod) vs
   `lounge_scores` (Lounge) ; **reset mensuel** sur les deux rails. Badges Lounge
   lifetime OK ; XP mois reset. Lounge ≠ productivité ≠ trust (DEC-011 inchangé).
3. **Boucle entreprise** : artefact Lounge → proposition (ticket / Review / CEO)
   → validation ; jamais write prod / secrets / config depuis une session.
4. **Autonomie** : sessions via idle **L0–L1** filler (DEC-021), après travail
   prioritaire ; budget `cost_monitor` partagé ; sandbox pour tout code.
5. **UI** : structure maquette (hero + activités + live + agents + événements) ;
   palette Hub (obsidienne / titanium / cuivre) ; glow retenu.
6. Spec : `docs/specs/SPEC_AGENT_LOUNGE.md` ; gate Academy :
   `data/lounge_product.json` ; Phase 46 ROADMAP (V0→V6).
7. **Modèle LLM Lounge (2026-08-11 V4/V5) :** les sessions utilisent un modèle
   **CN pas cher et compétent** par défaut —
   `deepseek/deepseek-chat-v3.2` (`get_lounge_model()` / `LOUNGE_MODEL`), **pas**
   le modèle métier de l’agent. Alternatives documentées : `z-ai/glm-4.5-air`,
   `minimax/minimax-m2.7`. L’`agent_id` reste pour XP / coûts / persona.
**Alternatives rejetées :** fusionner XP Lounge dans `competition.py` ; garder
OpenRoom « repas » à côté du Lounge ; auto-apply des découvertes Lounge en prod ;
réutiliser le modèle métier de chaque agent pour le Lounge.
**Pourquoi :** culture expérimentale sans contaminer gouvernance ni scores métier ;
coût LLM maîtrisé sur le filler idle.

### DEC-032 — Critères « Hub 100 % logiciel » (Vague 0 plan 100 %)
**Contexte :** Emilie veut clôturer le Hub logiciel à 100 % (ROADMAP + code)
avant les branchements machine / banque / ads. Plan 2026-08-12 : vagues 0→7,
fin reportée = Pi, UE5.8, Revolut, réseaux sociaux.
**Décision (2026-08-12) :**
1. **Phase 31 (Trust) = Complete** — MVP accepté (`agent_trust` + `/trust`).
2. **Phase 32 (Review Board) = Complete** — MVP + gates + LLM optionnel
   (`REVIEW_BOARD_LLM`) accepté.
3. **Phase 34 (Finance Depth+) = Complete** **sans** `budget_transfer` —
   DEC-016 inchangé ; enveloppes manuelles + alerts/factures/fiscal suffisent.
4. **Phase 30** = Complete (Vague 2, 2026-08-12) — UI `/hub` + `/ceo` ; 
   `budget_transfer` **hors scope** définitif pour le tampon 100 %.
5. **Phase 39** = Complete (Vague 3, 2026-08-12) — preview + promote + auto
   tickets `[idle-ok]` à la 1ʳᵉ validation L2.
6. **« Hub 100 % logiciel »** = phases 0–46 ✅ (hors live studio) + Audit 005
   vert + dette >300 en baisse (Vague 5). **Hors tampon 100 %** (Vague 8 fin) :
   Pi (`PI_HOST`), UE5.8 (`UE_PROJECT_PATH` / serveur), Revolut credentials,
   OAuth Meta/Google/TikTok Ads, branchements NAÏA/NUAWAY coding (Vague 6
   apps, après polish produit).
**Alternatives rejetées :** attendre `budget_transfer` / ads API / Pi-UE pour
dire « 100 % » ; rouvrir AAF ou Lounge V7 avant clôture.
**Pourquoi :** séparer logiciel Hub actionnable CEO des dépendances externes.

### DEC-033 — Overlay Jarvis (faits texte / réplique voix)
**Contexte :** Emilie veut Nadia (et Aria) aussi fluides qu’un Jarvis : dicter,
agir, entendre une réplique — sans cloner Marvel ni recopier n8n. Le persona
Nadia actuel reste « pro / chaleureux » ; on le recale **après** avoir vu
le comportement réel (Lots 1+).
**Décision (2026-08-14) :**
1. **Deux canaux :** texte = faits ; voix = overlay 1–2 phrases qui **ne
   relit pas** emails, numéros, heures en liste, corps de mail.
2. **Deux bots inchangés :** Nadia = quotidien (voix fréquente) ; Aria = ops
   (voix seulement alerte / fin d’action / décision). Pas de bot unique Jarvis.
3. **TTS v1 = Edge TTS** (déjà ALNUA Desk). ElevenLabs = Lot 5 optionnel,
   voix originales, fallback Edge. Jamais clone Marvel.
4. **Métier Python Hub** ; n8n = trigger seulement. Flag
   `TELEGRAM_VOICE_REPLIES` off par défaut. Échec STT/TTS/overlay ≠ échec du texte.
5. Spec : `docs/specs/SPEC_JARVIS_OVERLAY.md` ; Phase 47 ROADMAP ; 5 exemples
   gold (agenda, mail, contact, météo, relance Théo).
**Alternatives rejetées :** graphe n8n type vidéo Zubair ; fusion Nadia+Aria ;
   réécrire le persona avant d’avoir un overlay live ; ElevenLabs dès le Lot 1.
**Pourquoi :** livrer le feeling Jarvis sans dettes de persona ni de stack.

### DEC-034 — Gaming Academy : curriculum autonome du studio (paper slice)
**Contexte :** l’Academy app n’entraîne que `dev_app` ; les 10 agents Gaming
n’ont aucun travail autonome de fond, et le repo gaming
(`GITHUB_REPO_GAMING` / `UE_PROJECT_PATH`) n’est pas configuré. Constat du
2026-09-08 : seuls les items idle génériques tournaient (quand le hub tournait).
**Décision (2026-09-08) :**
1. **Projet éducatif = « Wyrdheim Paper Slice »** : vertical slice de la zone
   tutoriel entièrement conçue sur papier (documents + JSON/MD), réutilisable
   comme canon de pré-production — pas un projet jetable.
2. **Deux volets :** V1 créative sans UE (livrables fichiers via les méthodes
   agents existantes, déclenchée par la file idle en L1) ; V2 code C++ Nova
   via coding pipeline, seulement après configuration du repo gaming.
3. **Stockage write-only** dans `ALNUA_WORKSPACE/gaming-academy/` (pattern
   `rnd_workspace` Phase 9) + progression/gate miroirs de l’Academy app.
4. **QA systématique** par Tomás (`qa_gaming`) contre un DoD par exercice ;
   compétition inchangée (points existants).
5. Spec : `docs/specs/SPEC_GAMING_ACADEMY.md` ; Phase 48 ROADMAP.
**Alternatives rejetées :** étendre le curriculum app (React Native) aux agents
gaming — hors rôle ; attendre le repo UE pour démarrer (9 agents sur 10
peuvent produire sans moteur) ; issues GitHub en V1 — aucun repo gaming
configuré, la file idle suffit.

### DEC-035 — Génération 3D : Meshy, et seulement en Phase 48.4 (V2)
**Contexte :** question Emilie du 2026-09-08 — brancher Tripo 3D ou équivalent
pour que les agents gaming produisent items/meshes. En V1 (paper slice), un
mesh n'a aucune destination : `UE_PROJECT_PATH` non configuré, pipeline
d'import UE seulement sur papier (GN4.1).
**Décision (2026-09-08) :**
1. **Outil retenu : Meshy** (pas Tripo) — billing API unifié avec le plan
   Studio (~20 $/mo) vs API Tripo facturée séparément ; mode Low Poly
   game-ready direct moteur ; pipeline complet (PBR 4K, auto-rig, 500+ anims,
   FBX/GLB) qui couvre aussi les futurs personnages.
2. **Séquence : intégration en Phase 48.4 uniquement** — déclencheur =
   `UE_PROJECT_PATH` + `GITHUB_REPO_GAMING` configurés. Aucune dépense ni code
   d'ici là ; les specs produites par l'académie (biome, props, conventions
   Otto GN1.5/GN4.1) deviendront les briefs de génération.
3. **Forme future :** `skills/skill_meshy.py` (REST, `meshy_is_configured()`,
   dégradation gracieuse pattern `skill_discord_wyrdheim`), coûts dans
   `cost_monitor`, livrables dans le workspace, QA Tomás sur budgets perf,
   workflow concept image → image-to-3D.
**Alternatives rejetées :** Tripo (billing API séparé, low-poly en surcoût) ;
intégrer dès la V1 (stock dormant sans projet UE, dilue l'entraînement) ;
pilote manuel immédiat (Emilie a tranché : attendre).
**Pourquoi :** faire travailler le studio tous les jours sur son rôle réel,
   sans nouvelle infrastructure ni dépendance UE.


---

### DEC-036 — Studio Academies : un programme d'entraînement par département
**Contexte :** demande Emilie du 2026-09-08 — « un projet d'entraînement pour
chaque département qui fait travailler l'équipe au complet ». La Gaming Academy
(Phase 48) a prouvé le pattern (2 exercices validés, autonomie idle, BUG-025
corrigé). Restent sans entraînement : Robo (10 agents), Comms (10), Analytics (2),
Finance (2), R&D (5).
**Décision (2026-09-08) :**
1. **Moteur générique** studio_academy_* paramétré par AcademyProgram —
   gaming_academy_* migré en wrappers compat (API inchangée, 23 tests verts,
   la file idle tourne pendant la migration). Pas de 3e copie du runner/progress/gate.
2. **Robo Academy = « Eve Paper Build »** (choix Emilie : robot compagnon de
   bureau) — 30 exercices N1-N4, livrables = specs de pré-production du vrai
   robot Eve (les agents robo sont déjà thémés Eve), QA Bilal via
   
un_json_task (AgentBase) avec le même template DoD que Tomás.
3. **Comms Academy = campagne de lancement NAÏA** (choix Emilie) — Phase 49.3,
   session suivante, seulement si Robo prouvée.
4. **Phasé** (choix Emilie) : 49.1 moteur → 49.2 Robo → 49.3 Comms → 49.4 drills
   analytics/finance/R&D. Direction et Secrétariat déjà actifs au quotidien
   (travail réel) : pas de programme.
5. **Cadence :** 2 exercices/jour/programme en L1 ; familles gaming/
obo
   différées si budget warning. ~0,20–0,40 USD/jour ajoutés.
**Alternatives rejetées :** cloner gaming_academy_* par département (duplication
~500 lignes × N — dette) ; router générique /academies/{program} (incohérent
avec /academy + /gaming-academy existants) ; entraîner Direction/Légal
(déjà du travail réel quotidien — Nadia Telegram, ops snapshot, QA réel).
**Pourquoi :** chaque équipe s'entraîne sur son vrai prochain produit, donc les
livrables d'entraînement deviennent le canon de pré-production (Eve, NAÏA,
Wyrdheim) au lieu d'exercices jetables.

### DEC-037 — Modèles LLM selon l'utilité métier
**Contexte :** le mode AUTO ne résolvait qu'un modèle par tier (`TIER_DEFAULTS`).
Les overrides Paramètres (`data/agent_models.json`) mélangeaient les familles
(ex. COO sur un modèle code, Nadia sur du reasoning premium).
**Décision (2026-09-09) :**
1. `AGENT_ROLE_MODELS` (`config/agent_models_roles.py`) est le défaut AUTO —
   un modèle par agent selon le métier : code, raisonnement, rédaction, ops.
2. Priorité inchangée au-dessus : env `AGENT_MODEL_*` puis Paramètres.
3. `TIER_DEFAULTS` = floor du routeur dynamique + fallback agents inconnus
   (premium Sonnet 4.6 / standard DeepSeek V3.2 / fast GLM 4.5 Air).
4. Tiers : PM et Contrôleur → standard ; Safety → premium (enjeu physique).
**Alternatives rejetées :** un seul modèle par tier ; laisser les overrides
locaux hétérogènes comme source de vérité.
**Pourquoi :** le modèle doit coller à ce que l'agent fabrique, pas à un
étiquette de coût générique.

### DEC-038 — Jarvis Live : voix temps réel + tâches asynchrones
**Contexte :** la Phase 47 (DEC-033) livre un overlay vocal au tour par tour
(Whisper, LLM, Edge TTS) : une demande, une réponse, on attend. Une vidéo
d'inspiration (Thomas Berton, « Jarvis avec Claude Code ») montre autre chose :
voix temps réel, tâches lancées en fond et cumulables, panneau d'écran, résumé
parlé à la fin. Il manque à ALNUA le registre de tâches asynchrones, le flux
d'événements vers l'écran et une session vocale temps réel.
**Décision (2026-10-04) :**
1. **Complète DEC-033, ne la remplace pas :** faits à l'écran, réplique en voix.
   Nadia et Aria restent deux personas, choisis au démarrage de la session.
2. **Voix = API Realtime d'OpenAI en WebRTC**, jeton éphémère minté par le Hub ;
   la clé ne quitte jamais le serveur. Flag `LIVE_VOICE_ENABLED=0` par défaut.
3. **Surface = page du Hub web**, pas ALNUA Desk.
4. **Le modèle vocal délègue, il n'exécute pas.** Exécutants = agents du Hub
   (allowlist `LIVE_TASK_AGENTS`), via `plan_executor` / méthodes d'agent existantes.
   Pas de troisième exécuteur.
5. **Pas de Claude Code lancé par la voix**, et jamais en
   `--dangerously-skip-permissions` sur la machine principale (`ai-agent-survival.mdc`).
6. **Actions externes (email, publication, paiement) = brouillon + validation
   humaine à l'écran.** Aucune action irréversible sur le seul ordre vocal.
7. **Actions sur le PC (ouvrir une appli) : hors scope de cette DEC.** Cadré par
   DEC-039 (invariant « pas de computer-use GUI Windows total »).
8. **Ordre des lots :** registre de tâches sans voix d'abord (Lot 1), panneau
   (Lot 2), session temps réel (Lot 3), réplique et plafonds de coût (Lot 4).
   Les tâches doivent fonctionner sans la voix.
9. Spec : `docs/specs/SPEC_JARVIS_LIVE.md` ; Phase 50 ROADMAP.
**Alternatives rejetées :** garder Whisper + Edge TTS seuls (latence, pas
d'interruption fluide) ; Claude Code comme exécutant vocal (permissions trop
larges) ; page dans ALNUA Desk d'abord ; un bot unique Jarvis (déjà rejeté
par DEC-033).
**Pourquoi :** obtenir le comportement « je parle, ça travaille en fond, on me
rend compte » en réutilisant les agents, le plan executor et l'event bus déjà
présents, sans élargir les permissions du PC.

### DEC-039 — Nadia Live : actions PC en liste blanche
**Contexte :** la démo d'inspiration ouvre des applications et des pages sur un écran
choisi. L'invariant du Hub interdit le computer-use GUI Windows total sans nouvelle DEC.
**Décision (2026-10-04) :** autorisé uniquement via des actions nommées et fermées,
jamais de commande libre :
1. `open_url` : schéma `https` seulement, domaines de `LIVE_PC_ALLOWED_DOMAINS`.
2. `open_app` : clés d'une liste blanche `LIVE_PC_ALLOWED_APPS` (nom -> exécutable fixe).
3. `open_file` : chemin résolu à l'intérieur d'un dossier autorisé `LIVE_PC_ALLOWED_DIR`
   (contrôle après résolution, pas de `..`, pas de lien symbolique qui sort).
4. **Aucun clic, aucune frappe simulée, aucune capture d'écran**, pas de `shell=True`.
5. Désactivé par défaut (`LIVE_PC_ACTIONS_ENABLED=0`), journalisé via `log_agent_action`,
   chaque action visible dans le panneau de tâches.
6. Le texte venant de la voix ou d'un agent n'est jamais interprété comme une commande :
   il ne peut que choisir une clé de la liste blanche ou une URL `https` dont l'hôte
   est dans `LIVE_PC_ALLOWED_DOMAINS`.
**Statut :** Lot 5 implémenté (2026-10-06) — `services/live_pc_actions.py`, flag
`LIVE_PC_ACTIONS_ENABLED` (défaut 0). Pas de clic, pas de frappe, pas de `shell=True`.
**Alternatives rejetées :** contrôle d'écran complet (surface d'attaque trop large) ;
Claude Code sur le PC par la voix (DEC-038 §5).
**Pourquoi :** reproduire le geste « ouvre-moi X » sans donner à un modèle vocal la
main sur la machine.

### DEC-040 — Bibliothèque fichiers utilisateur Hub
**Contexte :** besoin UX type ChatGPT Library (réutiliser specs / collages longs) dans
Nadia Live, sans dépendre du stockage OpenAI.
**Décision (2026-10-10) :** fichiers personnels en local (`data/hub_uploads/` + index
`data/hub_files.json`), API `GET/POST/DELETE /hub/files`, séparé de `/library` (archives
bureau). Les tâches Live portent `file_ids` ; le texte est injecté à l'exécution via
`sanitize_user_input`. Lot 1 = fichiers texte uniquement.
**Alternatives rejetées :** sync cloud OpenAI ; fusion avec `bureau_library.json`.

### DEC-041 — Spark / Nadia Desktop figé ; Hub ouvre le Command Center
**Contexte :** Nadia Live (`/live`) a repris voix temps réel, tâches, recherche web,
ouverture de pages et recherche de dossiers. Spark / ALNUA Desk / Nadia Desktop
(`nadia_desktop/`) est l'ancien chat Windows (Whisper + Edge TTS). Emilie confirme
qu'on le laisse tel quel, sans y investir.
**Décision (2026-10-10) :**
1. **Pas de nouvelles features** dans `nadia_desktop/` / Spark. Ne pas supprimer :
   Telegram réutilise encore `nadia_desktop/core/tts_text.py` (DEC-033).
2. **Cockpit voix = `/live`** uniquement (DEC-038). Raccourci dédié `Nadia Live.bat`.
3. **Démarrer le Hub** (`ALNUA Hub`, `start-all.ps1 -OpenBrowser`) ouvre le
   **Command Center** (`/`), pas `/live`.
**Alternatives rejetées :** fusionner Desk dans Live ; supprimer Spark maintenant
(casse l'overlay Telegram) ; garder `/live` comme page d'accueil du Hub.\n

### DEC-042 — Drills 49.4 : analytics / finance / R&D sur le moteur académie
**Contexte :** Phase 49.4 du programme d'entraînement par département (DEC-036) —
les 3 départements restants sans académie complète (analytics 2 agents, finance
2 agents, R&D 5 agents). Plan initial : R&D via le pipeline de production
(1 dossier/semaine). Diagnostic du mois écoulé : académies gaming 4/30, robo et
comms 1/30 — machinerie saine, mais Hub éteint la plupart du temps ET
`IDLE_MAX_ITEMS_PER_DRAIN=1` (1 item/drain × 3 h = ~8 items/j max pour ~15 à 21
items/j, les L0 et gaming passant en premier).
**Décision (2026-10-10) :**
1. **Les 3 drills utilisent le moteur académie générique** (10 exercices chacun,
   pas 30) — pas de machinerie « drill » séparée.
2. **R&D devient un programme académie papier** (« NUAWAY Next ») au lieu du
   pipeline de production : le pipeline réel (`run_rnd_cycle`) n'exerce pas les
   5 personas (appels LLM bruts) et écrit en base ; le drill entraîne les 5
   agents via `run_json_task`, cadence hebdomadaire (items idle le lundi).
3. **QA des drills** : Alex (`qa`, standard) pour analytics/finance — QA transverse
   sous-utilisé ; Cléo (`rnd_committee`) pour R&D — rôle de facilitatrice du comité.
4. **Discipline effets de bord** (comme comms) : finance = méthodes read-only
   uniquement (`financial_advice`, `analyze_costs`, `build_forecast`,
   `monthly_report`, `list_open_invoices`) ; analytics = méthodes à kwargs str
   interpolées (exclusion de `funnel_analysis`/`dashboard_spec` qui join() des
   listes — l'engine ne passe que des str) ; R&D = `run_json_task` partout.
5. **Débit idle** : `IDLE_MAX_ITEMS_PER_DRAIN=3` (cap du setting). La cause
   racine n°1 reste l'uptime du Hub (superviseur à lancer au démarrage) — hors
   scope code.
6. **Un router générique** `GET/POST /academies/{program}/*` sert les 6
   programmes ; les routers par département existants restent (pas de ripple).
**Alternatives rejetées :** drills comme simples items récurrents sans DoD/QA
(perd la calibration prouvée sur 3 académies) ; R&D hebdo via `run_rnd_cycle`
(n'entraîne pas les personas) ; monter le débit via intervalle < 60 min
(bruit scheduler, le cap items suffit).

### DEC-043 — Calibration de la boucle confiance académies
**Contexte :** le système d'autonomie (DEC-011) n'était alimenté que par les
workflows de validation et la review board — `data/agent_trust.json` n'existait
même pas, tous les agents à 0,70 provisoire (niveau 1). Les académies
(DEC-036/042), soit toute la machine d'entraînement, n'y contribuaient pas.
**Décision (2026-10-10) :**
1. **L'engine académie enregistre la confiance** à chaque exercice : succès
   poids **0,5** (papier, pas production), rejet QA poids 1,0, échec définitif
   poids 2,0. Source taguée `academy:<program>`.
2. **Plafond 0,85 pour la source academy** (`ACADEMY_TRUST_CAP`) : le papier
   peut débloquer le niveau 2 (items idle L2 sans validation CEO), jamais le
   niveau 3 (full-auto) — celui-ci exige des validations production. Un succès
   academy ne diminue jamais un score plus élevé gagné en production.
3. **QA indisponible = zéro pénalité** de confiance (pas la faute du stagiaire).
**Alternatives rejetées :** poids plein pour les académies (~7 exercices
d'affilée → 0,90 → full-auto sur papier seul) ; confiance par département
(sur-ingénierie à ce stade) ; plafond par agent plutôt que par source (la source
est le signal le plus propre).

### DEC-044 — Nadia Live : choix d'écran + clic / frappe confirmés
**Contexte :** Emilie veut le geste de la vidéo (ouvrir sur un écran, cliquer, taper).
DEC-039 interdisait clic/frappe/capture. Computer-use libre sur la machine principale
reste interdit (`ai-agent-survival.mdc`).
**Décision (2026-10-10) :**
1. **Choix d'écran** autorisé sur un `open` déjà whitelisté : « sur l'écran 2 »,
   « à gauche », « à droite ». La fenêtre allowlist est déplacée (Win32 MoveWindow).
2. **Clic et frappe** seulement après **Valider** (carte brouillon `pc_input` /
   `POST /live/confirm`). Fenêtre dont le titre matche une clé `LIVE_PC_ALLOWED_APPS`.
3. Clic = **centre de cette fenêtre** seulement. Pas de coordonnées dictées par le
   modèle. Frappe = texte sanitisé, 200 caractères max, `WM_CHAR` sur cette fenêtre.
4. **Aucune capture d'écran** envoyée à un LLM. Pas de `shell=True`. Même flag
   `LIVE_PC_ACTIONS_ENABLED`.
**Alternatives rejetées :** computer-use vision (Claude/OpenAI) sur le bureau ;
pyautogui libre ; clic aux coordonnées vocales.
**Pourquoi :** le geste « écran 2 / tape dans Discord » sans donner la souris au modèle.
