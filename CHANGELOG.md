## 2026-10-11 — Audit 006 : RCE Next.js critique corrigée, deps durcies

- **fix(deps)** : `next` **16.3.0 → 16.4.0** — ferme 9 advisories dont la
  critique GHSA-p293-qw3h-jr36 (RCE non authentifié sur serveurs hébergés
  **Windows** — cas du hub) et le RCE Image Optimization AVIF. Le pin exact
  `16.3.0` masquait le fix à `npm audit fix` (« outside stated range »).
  `eslint-config-next` aligné. `BUG-026`.
- **fix(deps)** : `vitest` 4.1.10 → 4.1.11 (path traversal `@vitest/mocker` —
  simple patch malgré la suggestion npm de forcer un major) ; `dompurify`
  direct 3.4.13 → 3.4.16 (2 XSS) ; `npm audit fix` non-breaking.
  **22 → 11 vulnérabilités (0 critical, 0 moderate)** ; résidu dev-only
  (`braces`/`fast-glob` dans outils lint/CLI) et `dompurify` niché sous
  `monaco-editor` (override refusé 3× — règle des 3 essais) documentés.
- **docs(audit)** : Audit 006 10 dimensions dans `docs/classeur/doc-audit.md`
  — verdict 🟢 (gouvernance/hygiène git 🔴→🟢 vs Audit 005) ; `BUG-026`/`028`
  corrigés, `BUG-027` ouvert (2 fichiers Phase 49-50 >300 lignes, paydown
  candidat) ; micro-drift `AGENTS.md` resync (53 personas) ; stats `BUGS.md`.
- Vérifs : `tsc --noEmit` 0 erreur, vitest **93/93**, pytest **852** passed /
  6 skipped, `ruff` 0 erreur.

## 2026-10-11 — Items idle L2 débloqués par la confiance (suite Phase 50)

- **feat(idle)** : un item L2 peut tourner sans validation CEO du jour si
  l'agent porteur est à trust ≥ 0,80 (bande autonomie 2, DEC-011) — override
  mesuré par agent dans `_item_eligible`, à côté du garde-fou self-dev ≥ 0,70.
  La validation CEO reste le déblocage maître ; un score en lecture échouée
  (0,0) laisse tout gâté.
- **observabilité** : `pick_next_item` expose `l2_trust_override` (ids des L2
  pris via la confiance) et la raison de skip nomme le score courant
  (`l2_needs_ceo_validation (trust 0.79)`).
- **tests** : `test_l2_trust_override_unlocks_academy_wake` + borne 0,79 ;
  `test_l2_blocked_until_ceo_validation` ajusté (0,9 → 0,75 : la politique
  change, L2 reste gâté sous 0,80). Suite 852 verts, ruff clean.
- Live : `dev_app` à 0,70 provisionnel → `academy_wake` reste gâté tant que la
  confiance n'est pas gagnée (6 validations académie/production environ).

## 2026-10-11 — Confiance agents visible dans le cockpit CEO

- **feat(autonomy)** : section `trust` dans `GET /autonomy/ceo-cockpit` —
  par agent : score, niveau d'autonomie (N0-N3), nombre de validations,
  seuil du palier suivant, dernière note ; plafond académie rappelé (0,85).
  Dégradé silencieux comme les autres sections du cockpit.
- **feat(web)** : panneau « Confiance agents » sur `/ceo` (`CeoCommandView`) —
  top 8 agents par score, barre colorée par bande DEC-011 (manager / Review
  Board / autonome), badge, nombre de validations, lien vers `/trust` ; état
  de chargement distinct et message d'erreur réel affiché. Le composant
  `CeoCockpitPanel` (non monté à ce jour) reçoit aussi un bloc `TrustBlock`
  branché sur la nouvelle section cockpit.
- `tests/test_ceo_cockpit_trust.py` (3 tests) ; suite 850 verts, ruff clean,
  `tsc --noEmit` clean. Suite naturelle de Phase 50 (DEC-043) réalisée.

## 2026-10-10 — Phase 50 : les académies alimentent la confiance (DEC-043)

- **feat(autonomy)** : chaque verdict QA d'académie met à jour la confiance
  agent (`record_validation`, source `academy:<program>`) — succès poids 0,5,
  rejet 1,0, échec 2,0. Avant, `agent_trust.json` n'existait pas : tout le
  monde au niveau 1 par défaut.
- **feat(autonomy)** : plafond par source `ACADEMY_TRUST_CAP=0,85` — le papier
  débloque le niveau 2 max ; le niveau 3 exige des validations production.
- `trust_score` dans le résultat de chaque exercice. QA indisponible = aucune
  pénalité. 10 tests (`test_academy_trust.py`), suite 834 verts. Relancer le Hub.
- **fix(tests)** : isolation hermétique du trust store — `HUB_REPO_PATH` redirigé
  vers un tmp de session dans `conftest.py` (le monkeypatch par test était
  contournable : la suite avait pollué le vrai `data/agent_trust.json` — store
  supprimé, il se reconstruit sur l'activité réelle). Suite 847 verts + CLEAN.

## 2026-10-10 — Mesures contenu et pubs : plus de zéros inventés

- **fix(skills)** : activité GitHub, builds Gaming et essais Robo sont lus
  pour de vrai. Sans token, sans dépôt ou si la base est illisible, la
  réponse est `available: false` — une semaine vide n'est plus le même
  signal qu'une source absente.
- **fix(ads)** : le rapport campagne prend la dépense des transactions
  liées. Impressions, clics et CTR de régie ne sont plus renvoyés à 0.
  Les analytics de post non branchées omettent les compteurs.
- **fix(idle)** : un kind inconnu passe en erreur au lieu d'être marqué
  terminé.
- **docs** : Phase 47 lot 5 ElevenLabs est codé, flag `ELEVENLABS_TTS` off.

## 2026-10-10 — Drills académie 49.4 : analytics, finance, R&D (DEC-042)

- **feat(academies)** : 3 drills sur le moteur générique (SPEC_STUDIO_ACADEMIES) —
  Analytics « Hub Autopsy » (analyst_business/analyst_data, 10 ex.), Finance
  « Budgets Projets Papier » (accounting/controller, 10 ex., read-only), R&D
  « NUAWAY Next » (brainstorm/rnd_agent/rnd_dossier/rnd_ceo/rnd_committee,
  10 ex. via `run_json_task`, items idle le lundi).
- **feat(api)** : router générique `GET/POST /academies/{program}/*` (6 programmes).
- **fix(idle)** : `IDLE_MAX_ITEMS_PER_DRAIN=3` — le débit 1 item/drain affamait
  les académies (comms/robo bloquées à 1/30 en septembre). Familles budget :
  +analytics/finance/rnd différées sur warning.
- **test** : `tests/test_drill_academies.py` (18) ; suite 819 verts ; ruff clean.
  Fix bonus : import inutilisé dans `tests/test_hub_user_files.py`.
- **Diagnostic** : académies en pause sept.→oct. = Hub éteint (uptime), pas un
  bug. Superviseur à lancer au démarrage du PC. Relancer le Hub.
- **ops** : raccourci « ALNUA Hub » dans le dossier Démarrage Windows —
  `start-all.ps1` (superviseur :8003 + web :3000 + bots) se lance à l'ouverture
  de session, fenêtre minimisée (schtasks refusé par la politique machine).

## 2026-10-10 — Nadia Live : écran + clic/frappe confirmés (DEC-044)

- **feat(live)** : « ouvre Instagram sur l'écran 2 » (ou à gauche / à droite)
  déplace la fenêtre allowlist.
- **feat(live)** : « tape bonjour dans Discord » / « clique au centre sur Gmail »
  → brouillon + Valider. Centre de fenêtre seulement, pas de coordonnées libres,
  pas de capture d'écran envoyée à un modèle.
- Relancer le Hub (`LIVE_PC_ACTIONS_ENABLED=1` déjà requis).

## 2026-10-10 — Nadia Live : trous vidéo (effacer, HTML, Sofia, contexte)

- **feat(live)** : « tout effacer » à la voix et au clavier (écrans seulement).
- **feat(live)** : mini-appli HTML (chrono / compteur / notes / checklist) dans
  `data/live_html/`, ouverte dans le navigateur.
- **feat(live)** : brouillon LinkedIn rédigé par Sofia + voix marque ALNUA.
- **feat(live)** : les tâches reçoivent les derniers résultats d'écran (sources).
- Relancer le Hub.

## 2026-10-10 — Hub s'ouvre sur Command Center ; Spark figé (DEC-041)

- **ops** : `ALNUA Hub` / `start-all -OpenBrowser` ouvre `/` (Command Center),
  plus `/live`. Le raccourci Nadia Live reste l'entrée voix.
- **docs** : Spark / Nadia Desktop gelé — pas de nouvelles features (`DEC-041`).

## 2026-10-10 — Hub Files : secrétaire, voix, navigation Nadia

- **feat(assistant)** : chat CEO / secrétaire — bibliothèque + `file_ids` sur `/assistant/chat`.
- **feat(live)** : pièces jointes composer partagées avec `start_task` vocal ; barre Live / Bureau / Connexions.
- Relancer le Hub.

## 2026-10-10 — Bibliothèque fichiers Hub + pièces jointes Live (DEC-040)

- **feat(hub-files)** : API `/hub/files` (upload texte local, liste, suppression).
  Tâches Live acceptent `file_ids` ; contenu injecté à l'exécution (sanitisé).
- **feat(live)** : composer — bouton Bibliothèque, collage &gt; 5000 caractères → fichier auto.
- Relancer le Hub.

## 2026-10-10 — Nadia Live : chercher un dossier sur le PC

- **feat(live)** : « cherche / ouvre le dossier factures » parcourt Bureau,
  Documents, Téléchargements (pas tout le disque). Carte liste + ouverture
  Explorateur si un seul match. Pas d'exécutables, pas de `..`, pas de clic.
- Relancer le Hub.

## 2026-10-10 — Nadia Live : recherche internet en secondes, pas en minutes

- **fix(live)** : la recherche Live ne lance plus le pipeline R&D / DuckDuckGo bloquant.
  Timeout dur 10 s, sources réelles (Google News RSS, Wikipedia, DuckDuckGo Instant,
  Tavily si `TAVILY_API_KEY`). Pas d'invention si le web ne répond pas.
- **fix(live)** : « va sur / lance Instagram » ouvre le navigateur (liste blanche DEC-039).
  « lance une recherche… » n'est plus pris pour une action PC. Toujours pas de clic ni
  de frappe. Relancer le Hub.

## 2026-10-10 — Nadia Live Lot 6 : cartes, images, LinkedIn, créneaux

- **feat(live)** : cartes résultat liste / image / brouillon (bouton Valider).
  Agenda et mails s'affichent en liste. « Tout effacer » existait déjà.
- **feat(live)** : génération d'image via OpenRouter (`LIVE_IMAGE_MODEL`) et photos
  Wikimedia avec crédit. Fichiers dans `data/live_media/` (git-ignoré).
- **feat(live)** : brouillon LinkedIn puis publication seulement sur Valider /
  « publie le post ». Créneaux libres 9h–18h (rien n'est réservé tout seul).
- Relancer le Hub pour charger les routes `/live/confirm` et `/live/media`.

## 2026-10-06 — Nadia Live Lot 5 : Instagram, recherche, ouvrir une page

- **fix(live)** : la recherche internet affiche un brief avec sources au lieu de
  « N fiches archivées ». L'archive bibliothèque part en fond, elle ne bloque plus la tâche.
- **feat(live)** : Lot 5 DEC-039 — « ouvre Instagram / Gmail / YouTube » ouvre le navigateur
  sur une liste blanche HTTPS (`LIVE_PC_ACTIONS_ENABLED`). Pas de clic, pas de frappe.
- **fix(instagram)** : OAuth essaie `instagram` puis `instagram_business` ; Meta exige un
  compte Professionnel lié à une Page Facebook (un compte perso est refusé).
- Reste : valider OAuth dans le navigateur ; génération d'image OpenRouter ; relancer le Hub.

## 2026-10-06 — Secrétariat SAV, Direction dédoublée, Nadia Live hors Direction

- **fix(web)** : le SAV en bas du secrétariat était hors scroll (flex sans `min-h-0`).
- **fix(web)** : Direction (`/hub`) affichait deux fois les liens siège.
- **fix(web)** : l'appel Nadia (`/live`) passait dans le chrome Command Center (Direction).
  Il a son propre shell, rattaché au secrétariat.

## 2026-10-05 — Nadia Live : Gmail Connecter (lien OAuth)

- **fix(live)** : « Connecter Gmail » n'ouvrait rien — le lien Composio était noyé dans le texte
  d'instruction, et `window.open` après l'attente était bloqué. Le Hub renvoie une URL pure ;
  la fenêtre s'ouvre au clic ; un lien de secours reste affiché.
- Instagram : Nadia ne crée pas le compte (Meta). Compte professionnel dans l'app, puis OAuth.

## 2026-10-05 — Nadia Live : accès web/mail/socials + cartes résumé/graphique

- **feat(live)** : `GET /live/access` sonde internet + Gmail/Agenda/Discord/Instagram
  (sans secrets). `POST /live/connect/{app}` ouvre l'OAuth Composio (allowlist).
- **feat(web)** : bandeau Accès sur `/live` (Connecter Gmail, Agenda, Discord, Instagram).
  Cartes résultat `summary` et `chart` (recharts). Page Connexions propose aussi Calendar + Instagram.
- **feat(secretary)** : « connecte discord / instagram » + livrables résumé/graphique structurés.
- Reste : l'OAuth doit être validé dans le navigateur ; Lot 5 PC (DEC-039).

## 2026-10-05 — Nadia Live Lot 4 : réplique de fin + plafond quotidien (Phase 50)

- **feat(api)** : plafond `LIVE_VOICE_MAX_MINUTES_PER_DAY` (429 + mode texte), `POST /live/session/end`
  et `GET /live/usage`. Durée bornée par l'horloge du Hub ; session oubliée = 5 min au prochain mint.
- **feat(web)** : Nadia annonce une tâche terminée ou un échec (sans relire le détail). Minutes
  restantes affichées. Session coupée quand le quota est épuisé.
- **chore** : `cost_monitor` journalise la durée (`seconds=N`) sans inventer un tarif audio.
- **test** : 6 tests Python + 4 tests web. Suite 750 Python, 76 web, ruff 0, tsc 0.
- Reste : Lot 5 (actions PC, DEC-039). Conversation réelle avec OpenAI toujours non testée.

## 2026-10-05 — Nadia Live : voix mains libres (Phase 50)

- **feat(voice)** : fini « Maintenir pour parler ». Le micro reste ouvert pendant la session,
  OpenAI détecte les tours de parole (`server_vad`) et on peut couper la parole à Nadia.
- **feat(web)** : bouton « Couper le micro », fermeture automatique après 90 s sans échange
  (une session ouverte consomme de l'audio même quand personne ne parle), annulation d'écho/bruit. Casque conseillé.
- **test** : 14 tests web (état piloté par le serveur, inactivité, mute), 8 tests Python.

## 2026-10-04 — Nadia Live Lot 3 : session vocale temps réel (Phase 50, DEC-038)

- **feat(api)** : `POST /live/session` crée un jeton éphémère OpenAI Realtime. Désactivé par
  défaut (`LIVE_VOICE_ENABLED=0`), la clé `OPENAI_API_KEY` reste sur le Hub. Instructions
  et outils fixés côté serveur (`services/live_session.py`).
- **feat(web)** : bouton « Démarrer la voix » (Nadia ou Aria), WebRTC en push-to-talk
  (micro coupé sauf bouton maintenu), interruption, transcription, orbe qui suit l'état.
  **Révisé le 2026-10-05** : mains libres à la demande d'Emilie (voir ci-dessous).
  Outils `start_task`, `list_tasks`, `get_task_status`, `cancel_task` branchés sur `/live/tasks`.
- **test** : 8 tests Python + 13 tests web (connexion simulée, push-to-talk, refus d'une
  adresse non OpenAI, outils). Suite 744 Python, 71 web, ruff 0, tsc 0.
- Non vérifié : conversation réelle avec OpenAI (aucune clé utilisée). Noms d'événements
  serveur à confirmer au premier essai (spec §11).
- Reste : Lot 4 (réplique vocale à la fin d'une tâche, plafonds de coût), Lot 5 (actions PC, DEC-039).

## 2026-10-04 — Nadia Live Lot 2 : cockpit web (Phase 50, DEC-038/039)

- **feat(web)** : page `/live` (lien depuis `/secretary`) — panneau de tâches avec durée
  en direct et annulation, cartes de résultat (texte, étapes d'un plan, erreur) rendues
  en texte React, « Tout effacer » sans toucher aux tâches, repli clavier
  (Nadia / Aria / Équipe). Flux SSE reconnecté automatiquement. Persona affichée : Nadia.
- **fix(api)** : `GET /live/tasks/stream` répond `Cache-Control: no-cache, no-transform` ;
  sans cela le proxy Next.js compressait le flux et les mises à jour arrivaient en retard.
- **docs** : DEC-039 (actions PC en liste blanche, non implémentée, Lot 5) ; spec :
  fournisseur d'image = OpenRouter, Done Lot 2, correction de la note sur `EventSource`.
- **test** : tests Python scindés (`test_live_tasks.py`, `test_live_tasks_api.py`,
  `live_tasks_fixtures.py`), 23 tests ; 16 tests web. Suite 736 passés, ruff 0, tsc 0.
- Reste : Lot 3 (session WebRTC), Lot 4 (réplique vocale, plafonds), Lot 5 (actions PC).

## 2026-10-04 — Jarvis Live Lot 1 : tâches asynchrones (Phase 50, DEC-038)

- **docs** : `SPEC_JARVIS_LIVE.md` + DEC-038 — voix temps réel (OpenAI Realtime) +
  tâches en fond, inspirées d'une vidéo « Jarvis avec Claude Code ». Complète
  DEC-033, ne la remplace pas. Pas de Claude Code lancé par la voix.
- **feat(api)** : `/live/tasks` (création, liste, lecture, annulation), `/live/agents`,
  flux SSE `/live/tasks/stream`. Exécutants = `coo`, `secretary`, `plan`
  (`run_coo_plan`), allowlist `LIVE_TASK_AGENTS`, concurrence `LIVE_TASK_MAX_CONCURRENT`.
- **feat(services)** : `live_tasks*.py` — état persisté (`data/live_tasks.json`,
  git-ignoré), tâches actives marquées `failed: interrupted_by_restart` au redémarrage,
  `done` seulement si le résultat existe vraiment, résultat tardif écarté après annulation.
- **test** : `tests/test_live_tasks.py` (22). Suite complète 735 passés, ruff 0.
- Lots 2–4 (panneau web, session WebRTC, réplique vocale) : pas commencés.

## 2026-09-09 — AUTO = pins Paramètres CEO (par agent)

- **fix(config)** : `AGENT_ROLE_MODELS` reprend les choix Paramètres
  (Gemma 31B Aria/Léon, GLM 5.2 Nadia/Hao, MiniMax M3 Théo/Idris/Camille,
  Qwen Coder Nova/Zara, R1 Sam/Finn/Layla, Haiku Jules/Rémi, Gemini 2.5 Mira/Iris).
  Les agents non pinés suivent les mêmes familles. `data/agent_models.json` restauré.

## 2026-09-09 — Catalogue OpenRouter à jour (Claude 5 / GPT-5.6 / GLM 5.3)

- **feat(config)** : Paramètres expose les slugs live OpenRouter — Claude Sonnet 5,
  Opus 5, Fable 5.1 ; GPT-5.6 Sol / Terra / Luna (+ Pro) ; GLM 5.3 / 5.3 Flash ;
  Kimi K3 (pas de K4 chez OpenRouter) ; MiniMax M3 déjà présent ; Gemini 3.1 Pro,
  DeepSeek V4, Grok 4.5–4.20.
- **feat(auto)** : `TIER_DEFAULTS` → Sonnet 5 / GPT-5.6 Terra / GLM 5.3 Flash.
  AUTO métier : Aria = Opus 5, specs/brand/legal = Sonnet 5, Nadia = GLM 5.3 Flash.

## 2026-09-09 — Modèles agents selon l'utilité (DEC-037)

- **feat(config)** : `AGENT_ROLE_MODELS` — AUTO n'est plus un modèle unique
  par tier. Code (Codex / Kimi K2.7 / Qwen Coder / Gemma 31B / Devstral) pour
  les builders ; raisonnement (Gemini 2.5 Pro, GLM 5.2, R1, MiniMax M3) pour
  direction/R&D ; rédaction (Gemma 26B, Sonnet 4.6) pour Comms ; ops cheap
  (GLM 4.5 Air) pour Nadia/Clara.
- **fix(tiers)** : PM et Contrôleur passent en standard ; Safety en premium.
  `TIER_DEFAULTS` : Sonnet 4.6 / DeepSeek V3.2 / GLM 4.5 Air.
- **ops** : `data/agent_models.json` remis à `{}` pour que AUTO applique
  les modèles métier (Paramètres peut toujours pinner).
- **test** : `tests/test_agent_models.py`.

## 2026-09-09 (nuit) — Comms Academy « Lancement NAÏA » (Phase 49.3)

- **feat(comms)** : 3e programme du moteur `studio_academy` — 30 exercices N1-N4
  pour les 10 agents Comms Hub : campagne complète de lancement NAÏA sur papier
  (stratégie, éditorial, teasers, brand kit, ads, presse) dans
  `comms/naia-launch/`. QA Élise (brand) via le chemin générique du moteur.
- **sécurité/dicipline** : les méthodes à effets de bord production
  (`create_campaign` → table `campaigns` + capability `ads:spend`,
  `generate_posts`/`draft_*` → files de posts) ne sont JAMAIS appelées par
  l'académie — entraînement via `handle_instruction`, `run_json_task`
  (AgentBase) ou méthode papier dédiée. Test-garde
  `test_curriculum_never_touches_production_side_effects`.
- **feat(rnd_visual)** : `design_visual_concept` — Max (orchestrateur pur sans
  méthode LLM propre) gagne une vraie capacité de direction visuelle sur papier
  (LLMClient direct, system prompt inline — absent du specs registry).
- **feat(engine)** : `_build_kwargs` gère `run_json_task` (action/prompt/
  learning_key) — chemin d'entraînement générique sans effets de bord.
- **feat(api)** : router `/comms-academy` ; +2 items idle `comms_academy_exercise`/jour
  (L1, famille `comms` différée si budget warning).
- **fix(tests)** : `test_l2_blocked_until_ceo_validation` — fenêtre de pick élargie
  (10 → 25) : les 6 items L1 des 3 académies saturaient la fenêtre de 10 et
  masquaient le déblocage L2 après validation CEO.
- **test** : `tests/test_comms_academy.py` (17 tests, dont vérification AST des
  signatures avec résolution `run_json_task` sur AgentBase) ; suite 705 passed ;
  ruff propre.
- **Preuve live** : CN1.1 (Camille, stratégie lancement NAÏA — CrewAI, 2e agent
  non-AgentBase prouvé depuis BUG-025) validé par Élise au premier passage.

## 2026-09-08 (soir) — Studio Academies : moteur générique + Robo Academy (Phase 49.1/49.2)

- **feat(services)** : moteur `studio_academy` générique (`studio_academy_program`
  registry + `studio_academy_state` progression + `studio_academy_engine` runner +
  `studio_academy_gate` gate), paramétré par `AcademyProgram` — DEC-036.
  `gaming_academy_*` migré en wrappers compat : API publique inchangée, 23 tests
  gaming verts sans modification, file idle gaming non interrompue.
- **feat(robo)** : Robo Academy « Eve Paper Build » — 30 exercices N1-N4 pour les
  10 agents Hardware Workshop, livrables = specs de pré-production du vrai robot
  compagnon Eve (`hardware/eve-paper-build/`). QA Bilal via le chemin QA générique
  du moteur (`run_json_task` + contrat DoD, même template que Tomás).
- **feat(api)** : router `/robo-academy` (status, curriculum, gate, run-next,
  run/{id}) ; dispatch idle générique `*_academy_exercise` → `program.runner_module`.
- **feat(idle)** : +2 items `robo_academy_exercise`/jour en L1 ; famille `robo`
  différée si budget warning.
- **test** : `tests/test_robo_academy.py` (20 tests — dont vérification AST des
  kwargs du curriculum contre les vraies signatures des 10 agents, sans import LLM) ;
  suite complète 688 passed ; ruff propre.
- **Preuve live** : RN1.1 (Elin, identité produit Eve) validé par Bilal au premier
  passage ; endpoint `/robo-academy/status` opérationnel sur le hub redémarré.

# Changelog — ALNUA Hub

> Reconstitué rétroactivement le 2026-07-25 depuis `git log` (68 commits, historique
> depuis 2026-06-11) lors du bootstrap de gouvernance. Regroupé par date/thème plutôt
> qu'un commit par ligne — le détail exact reste dans `git log`. À partir de
> maintenant, ajouter une entrée par sprint/lot de changement au fur et à mesure,
> pas en dump différé. **Règle (Audit 002 / Phase A) :** tout merge ou commit
> >500 lignes de diff doit avoir au minimum une bullet dans ce fichier le jour même.

## 2026-09-08 — Phase 48.2 Gaming Academy : autonomie idle + fix CrewAI (feat/fix)

- **Type :** feat/fix
- **File idle (DEC-021) :** 2 items `gaming_academy_exercise` L1 par jour dans
  `idle_work_plan.py` ; dispatch dans `idle_work_recipes.py::_execute_one` →
  `run_next_exercise()` ; famille `gaming` différée si budget warning
  (`idle_work_queue.py`). Vérifié en direct : file 2026-09-08 = 11 items, drains
  réels exécutés (ops, budget, drafts, gaming routé vers le runner).
- **API :** nouveau router `api/routers/gaming_academy.py` (prefix `/gaming-academy`)
  — `GET /status` `/curriculum` `/gate`, `POST /run-next` `/run/{id}`. Enregistré
  dans `ALL_ROUTERS` (87 routers).
- **BUG-025 (haute) — cause racine « les agents gaming ne travaillent jamais » :**
  `crewai_additional_params` passait `session_id`/`cache_control` en kwargs au
  client OpenAI via CrewAI → `TypeError` à chaque appel de tout agent CrewAI
  (Mira, Nova…). Fix `extra_body` + test de régression. Prouvé en prod : GN1.1
  (Mira, vision zone tutoriel) exécuté via le hub → livrable validé par Tomás.
- **Tests :** +6 (plan, éligibilité budget, dispatch recipe, endpoints) + 1
  régression prompt-cache. Suite complète : **668 passed**, ruff propre.
- **État academy gaming :** 2/30 exercices validés (GN1.1 Mira, GN1.3 Finn),
  prochain = GN1.2 (Sable, dialogues PNJ mentor). Cadence autonome : 2/jour via
  les drains idle (toutes les 180 min).

## 2026-09-08 — Phase 48.1 Gaming Academy : moteur + preuve bout-en-bout (feat)

- **Type :** feat/test
- **Contexte :** suite spec 48.0 (DEC-034) — rendre le studio gaming autonome sur
  un projet éducatif « Wyrdheim Paper Slice », miroir de l'Academy app.
- **Nouveaux services :**
  - `services/gaming_academy_curriculum.py` — 30 exercices N1→N4 couvrant les
    10 rôles gaming, DoD par exercice, refs croisées N2+, `exercise_sort_key`
    numérique (le tri lexicographique plaçait GN1.10 avant GN1.2).
  - `services/gaming_academy_progress.py` — état `data/gaming_academy_progress.json`,
    miroir `academy_progress.py` ; statuts in_progress/rejected/validated/failed,
    cap 3 tentatives, tracking `canon_conflict`.
  - `services/gaming_academy_runner.py` — dispatch local 10 agents gaming
    (hors `agent_pipeline_registry`, isolation ripple), exécution méthodes réelles,
    rendu markdown, versioning write-only `-vN`, boucle QA avec injection du
    feedback, points compétition (`task_completed` + `task_validated`).
  - `services/gaming_academy_gate.py` — 5 checks (succès ≥65 %, N3 complet,
    couverture 10/10 rôles, canon clean, prérequis V2 env) + readiness %.
- **Agent :** `agents/qa_gaming_agent.py::review_deliverable` — revue DoD par
  Tomás (run_json_task). Calibrée après 3 rejets en boucle : le juge notait sur
  des critères hors DoD et changeait de barre à chaque itération ; le verdict
  est désormais strictement lié au DoD + canon, le reste devient suggestion.
- **Fix harness révélé par la preuve :** le renderer markdown dupliquait le
  premier champ string des dicts en liste (head + ligne détail) — artifact que
  Tomás relisait et sanctionnait. Corrigé + nested lists sur lignes dédiées.
- **Preuve bout-en-bout :** GN1.3 (Finn, quête « Premiers Pas ») exécuté en
  vrai : LLM Finn → livrable workspace → QA Tomás → `validated` → progression
  1/30, success 100 %, manifest workspace à jour, 6 versions préservées.
- **Tests :** `tests/test_gaming_academy.py` — 17 tests (intégrité curriculum,
  cycle progress, runner mocké, versioning write-only, gate). Suite complète :
  661 passed, ruff propre.

## 2026-09-08 — Rétablissement autonomie Hub + spec Gaming Academy (fix/docs)

- **Type :** fix/docs
- **Diagnostic autonomie (pourquoi un seul agent travaillait) :**
  - Hub lancé manuellement (hors superviseur) depuis ~04:18, scheduler muet —
    le superviseur officiel était arrêté depuis le 2026-08-20 ; file idle figée
    au 16 août (`data/idle_queue.json`).
  - `.env` : `REPO_PATH_ACADEMY` pointait `C:\Dev\alnua-academy` (inexistant) →
    5 issues academy bloquées en silence ; corrigé vers `D:\Dev\alnua-academy`.
    `REPO_PATH_NOMAD` corrigé vers `D:\Dev\NUAWAY` (même cause).
- **Actions :** redémarrage via `scripts/restart-all.ps1` (chemin supervisé,
  auto-recycle) ; pipeline academy débloqué (5 issues en codage) ; file du
  jour validée CEO (4 tickets `[idle-ok]` promus, dont Wyrdheim GDD check et
  Eve BOM drift) ; drain idle vérifié de bout en bout ; scheduler confirmé
  autonome (tick academy_poll 09:27).
- **Docs :** `docs/specs/SPEC_GAMING_ACADEMY.md` + DEC-034 + ROADMAP Phase 48 —
  curriculum autonome du Gaming Studio (Wyrdheim Paper Slice), V1 créative
  sans UE, V2 C++ Nova après config `GITHUB_REPO_GAMING`/`UE_PROJECT_PATH`.
- **Fragilité connue constatée (non corrigée ici) :** flapping health API sous
  tempête de polling UI + `--limit-concurrency 40` (recycle superviseur =
  codages tués mid-run si 5/5) ; `UnicodeDecodeError` cp1252 dans le pipeline
  de codage ; escalade possible après 40 turns. À traiter dans un lot dédié.

## 2026-09-07 — Audit 005 + rattrapage post Phase 47 (feat/fix/docs)

- **Type :** feat/fix/docs
- **Contexte :** dernier commit poussé sur `origin/main` = `ba841ad`
  (2026-08-11) ; ce lot documente et committe ~27 jours de travail resté en
  local (voir `docs/classeur/doc-audit.md` Audit 005 et `BUGS.md` BUG-024).
- **Features accumulées depuis Phase 47 Lot 4, jamais journalisées :**
  - Agent Lounge : arène de jeu/puzzle inter-agents avec scores, tournois,
    salles (`services/lounge_*`, `api/routers/lounge.py`, `/lounge`).
  - Nadia Desktop « Spark » : refonte en shell desktop pywebview/WebView2
    (`nadia_desktop/`) — chat routé Hub → GLM direct → Ollama local, docs
    Hub, TTS/STT (`core/voice.py`), overlay vocal.
  - Vocal Telegram bout-en-bout (Nadia + Aria) : Whisper → pipeline agent →
    TTS Edge/ElevenLabs (`bots/telegram_*_voice.py`,
    `services/voice_overlay.py`, `services/overlay_tts.py`).
  - Security Sentinel : patrouille programmée + tracking des échecs
    d'authentification (`services/security_sentinel.py`,
    `data/security_patrol_last.json`, `data/security_auth_failures.json`).
  - Services de fond : `cross_dept_drain`, `idle_work_plan`,
    `agent_wake_queue`, `brand_voice_debate`, `secretary_weather`.
  - Lanceurs Windows consolidés (`LIRE-MOI.txt`, `ALNUA Hub.bat`, `Spark.bat`,
    `scripts/windows/`) — anciens `.bat` épars à la racine retirés.
- **Corrections Audit 005 (même lot) :**
  - `SEC-007` : `agents/secretary_instruction.py::handle_instruction` sanitize
    désormais l'instruction en entrée (`sanitize_user_input`,
    `redact_pii_enabled=False`) — protège tous les appelants (Telegram, Hub,
    **Nadia Desktop**) au même point d'entrée plutôt que de compter sur
    chaque appelant pour le faire.
  - `bots/telegram_secretary_handlers.py` : `print()` de debug → `logger.info`.
  - `BUG-020` : mock obsolète dans `tests/test_telegram_voice.py`
    (signature `agent_id` manquante) corrigé.
  - `BUG-021` : `department-routes-live.test.ts` désynchronisé de la refonte
    `/ceo`/`/secretary` (composants `CeoCommandView`/`SecretaryCommandView`
    remplaçant l'ancien `CeoMorningBriefCard`, supprimé car orphelin) —
    test remis à jour.
  - `BUG-022` : `npm audit fix` (web) — 4 vulnérabilités → 0.
  - Resync comptes : `ALL_ROUTERS` 40→**86**, `AGENT_PERSONAS` 50→**53**
    (`README.md`, `ROADMAP.md`, `docs/classeur/implementation-status.md`).
- **Vérifié après coup :** `ruff` 0 erreur ; `pytest` 638 passed / 6 skipped ;
  `npx tsc --noEmit` 0 erreur ; `vitest` 42/42 ; `npm audit` 0 vuln.

## 2026-08-23 — Fallback LLM local (feat)

- **Type :** feat
- **Details :**
  - Bascule automatique vers un modèle local (Ollama / LM Studio / vLLM
    OpenAI-compatible) quand OpenRouter renvoie HTTP 402 (crédits épuisés).
  - Nouveau module `services/local_llm.py` + config runtime `data/llm_connectivity.json`.
  - UI `/settings` → « Connectivité IA » : activation, toggle bascule, URL/nom du
    modèle, clé API optionnelle, bouton « Tester la connexion ».
  - Endpoints `GET/POST /settings/llm-connectivity` + `/test`.
  - Variables `.env` : `LOCAL_LLM_ENABLED`, `LOCAL_LLM_FALLBACK_ON_CREDIT`,
    `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`, `LOCAL_LLM_API_KEY`.

## 2026-08-14 — Phase 47 Lot 4 Aria vocal (feat)

- **Type :** feat
- **Details :**
  - Aria Telegram : vocal → Whisper, même pipeline COO que le texte.
  - Overlay vocal seulement si alerte / action / décision ; silence sur un état.
  - Bots Nadia et Aria inchangés (pas de Jarvis unique).

## 2026-08-14 — Phase 47 Lot 3 brief 8h + météo (feat)

- **Type :** feat
- **Details :**
  - Brief 8h Nadia : faits en texte + overlay vocal (sans relire le digest).
  - Météo en tool HTTP (`wttr.in`) — pas d'OpenRouter, pas de LLM local.
  - Recherche déjà tool ; overlay local + repli mots-clés si crédits à sec.

## 2026-08-14 — Phase 47 Lot 2 Desk overlay (feat)

- **Type :** feat
- **Details :**
  - ALNUA Desk lit l'overlay, plus le pavé à l'écran ; stop TTS à chaque envoi.
  - Repli local sans LLM (`VOICE_OVERLAY_LLM=0`) si OpenRouter est à sec.
  - Pas de modèle open source local (contrainte disque).

## 2026-08-14 — Phase 47 Lot 1 Nadia vocal Telegram (feat)

- **Type :** feat
- **Details :**
  - Vocal Telegram → Whisper → même pipeline Nadia que le texte.
  - Overlay LLM : réplique parlée sans relire faits (DEC-033).
  - Edge TTS en note vocale ; flag `TELEGRAM_VOICE_REPLIES` (off par défaut).
  - Échec STT/TTS/overlay n'empêche jamais la réponse texte.

## 2026-08-14 — Phase 47 Lot 0 overlay Jarvis (docs)

- **Type :** docs
- **Details :**
  - Contrat faits-texte / réplique-voix pour Nadia et Aria (DEC-033).
  - Spec `docs/specs/SPEC_JARVIS_OVERLAY.md` + 5 exemples gold.
  - TTS v1 = Edge ; persona Nadia **pas** réécrit (après Lot 1 live).

## 2026-08-12 — Vague 5 dette Python ≤300 (refactor)

- **Type :** refactor
- **Details :**
  - Hotspots scindés : `idle_work_plan`, `schemas_agents_studio`,
    `telegram_secretary_handlers`, `agent_wake_queue`.
  - Packages Python : **0** fichier ≥300 (était 4) ; 0 >500 / >1000.
  - `get_pipeline_status` tolère GitHub 401 sans crash.
  - `ruff` OK ; `pytest` 597 passed / 4 skipped.

## 2026-08-12 — Vague 4 anti-mensonge résiduel (fix)

- **Type :** fix
- **Details :**
  - Backlog App : colonnes par priorité réelle (plus de votes/sprint/hash).
  - Missions partagées : assignee / points / avancement réels ; plus de
    risques / heures inventés.
  - Documentation App : champs bibliothèque réels (timing, topics) — plus de
    catégorie / projet / statut hashés.
  - SEO Marketing : libellé « non branché ».

## 2026-08-12 — Vague 3 Phase 39 idle polish (feat)

- **Type :** feat
- **Details :**
  - Validation CEO L2 → auto-promote tickets `[idle-ok]` une seule fois
    (`tickets_promoted_at` + toast `/ceo`).
  - Phase 39 ✅ (preview + promote déjà en place ; polish auto branché).

## 2026-08-12 — Vague 2 Phase 30 UI workflows (feat)

- **Type :** feat
- **Details :**
  - `HubWorkflowsPanel` monté sur `/hub` (ops / ship / recettes validation /
    historique + bandeau A_VERIFIER → `/ceo`).
  - Parcours CEO ↔ Direction lié ; Phase 30 ✅ (sans `budget_transfer`).
  - Test HTTP `waiting=a_verifier` + `approve-step`.

## 2026-08-12 — Vague 1 clôture doc Hub 100 % (docs)

- **Type :** docs
- **Details :**
  - Resync `implementation-status` (31/32/34/21/Lounge) + plan vagues 0–8.
  - `API_ROUTES` : emit/drain cross-dept ; SPEC workflow : `budget_transfer`
    abandonné pour tampon 100 % (DEC-032).

## 2026-08-12 — DEC-032 Hub 100 % logiciel Vague 0 (docs)

- **Type :** docs
- **Details :**
  - DEC-032 : critères 100 % Hub logiciel ; 31/32/34 closes ; 30/39 restent
    pour polish ; fin reportée = Pi / UE5.8 / Revolut / ads OAuth.
  - ROADMAP overview + Current phase alignés.

## 2026-08-12 — Phase 36 Depth+ cross-dept drain (feat)

- **Type :** feat
- **Details :**
  - Queue items avec `id` + statuts `queued|running|done|failed`.
  - `services/cross_dept_drain.py` — drain exécutable (launch plan / forecast /
    KPI sheet ou checklists) + artifacts `data/cross_dept_artifacts/`.
  - API `POST /cross-dept/emit-project`, `POST /cross-dept/drain` ; UI `/trust`.
  - Briefing COO enrichi (`done_count` / `recent_done`).

## 2026-08-11 — Détail projet anti-mensonge (fix)

- **Type :** fix
- **Details :**
  - Purge `mock-data` (phases/hash, features inventées, KPI agent) → `project-nav` only.
  - Vue d'ensemble : santé modules réels + synthèse live ; plus de Sprint faux / COO insight.
  - Modules / Équipe : empty states honnêtes quand le détail n'est pas en DB.

## 2026-08-11 — Vague D Gaming/Robo 100 % Hub (fix)

- **Type :** fix
- **Details :**
  - Analytics Gaming : FPS/crashs/draw_calls depuis `gaming_builds` ; plus de `pct()`.
  - Analytics Robo : télémétrie + lab réels ; manufacturing = « — ».
  - Projets/Backlog/Missions/Docs : données tickets/modules/topics réels.
  - Purge générateurs hash trompeurs ; Phase 21 Hub Complete.
  - Live studio (UE5.8 / Pi) reste config machine, pas faux chiffres UI.

## 2026-08-11 — Vague C Brand Depth+ (feat)

- **Type :** feat
- **Details :**
  - `brand_voice_debate` — débat LLM Élise (brand) ↔ Anouk (content_company).
  - `POST /brand/debate` + Brand Center « Débat Élise ↔ Anouk ».
  - Review Board LLM : sièges brand → débat dédié (`REVIEW_BOARD_LLM`).
  - Split `brand-view` (577 → hook + workspace panels).
  - Phase 35 Depth+ Complete.

## 2026-08-11 — Vague B produit égal — anti-mensonge UI (fix)

- **Type :** fix
- **Details :**
  - `/hub` : KPIs inventés → trust moyen + budget LLM live (ou « — »).
  - `/ceo` : objectifs %, réunions et jauge 78 % fictifs retirés.
  - Gaming/Robo analytics : badge **Démo** sur tuiles non branchées.
  - `/trust` : mini Review Board (`POST /review-board/evaluate`).
  - Briefing COO : flag déjà `=1` en local ; statut doc resync.

## 2026-08-11 — Agent Lounge V6 spaces + tournaments (feat)

- **Type :** feat
- **Details :**
  - 7 modules `lounge_activities/*` (arcade, strategy, puzzle, code Q&A,
    simulation, exploration, creative) + catalog unifié.
  - Runtime multi-activité ; idle rotation ; tournois seedés + API.
  - UI : toutes tuiles live, panneau play générique, events depuis API.
  - Phase 46 **Complete** (DEC-031).

## 2026-08-11 — Agent Lounge V5 propose + DeepSeek (feat)

- **Type :** feat
- **Details :**
  - Défaut LLM Lounge = `deepseek/deepseek-chat-v3.2` (CN pas cher) ;
    override `LOUNGE_MODEL` (GLM / MiniMax OK).
  - `POST /lounge/propose` → ticket Hub `source=lounge` + journal local ;
    UI « Proposer au département » après Puzzle.
  - Phase 46 V5 (DEC-031). Suite : V6 autres espaces.

## 2026-08-11 — Agent Lounge V4 idle + modèle fast (feat)

- **Type :** feat
- **Details :**
  - Idle `lounge_session` L0 filler (dernier dans la file) ; reporté si budget
    warning ; exécution puzzle via drain.
  - **LLM Lounge = tier fast dédié** (`get_lounge_model` / `LOUNGE_MODEL`) —
    pas le modèle métier de l’agent (DEC-031 §7).
  - Phase 46 V4. Suite : V5 propose → département.

## 2026-08-11 — Agent Lounge V3 Puzzle (feat)

- **Type :** feat
- **Details :**
  - Catalog puzzles + `lounge_runtime` sessions isolées ; XP via
    `challenge_won` / `session_completed`.
  - API `/lounge/puzzles`, `/lounge/sessions*` (start / run LLM / complete).
  - UI : tuile Puzzle « Jouer », panneau session, live dans le rail droit.
  - Phase 46 V3 (DEC-031). Suite : V4 idle `lounge_session`.

## 2026-08-11 — Agent Lounge V2 scores (feat)

- **Type :** feat
- **Details :**
  - `services/lounge_scores.py` — XP Lounge indépendant (reset mensuel, badges
    lifetime) ; API `/lounge/scores|leaderboard|profile` ; panneau classement live.
  - Strip agents : tous les agents (scroll horizontal), plus de plafond à 6.
  - Phase 46 V2 (DEC-031). Suite : V3 Puzzle jouable.

## 2026-08-11 — Agent Lounge V1 shell Hub (feat)

- **Type :** feat
- **Details :**
  - Page `/lounge` : hero ambiance, 7 tuiles activités (stubs), bande agents
    (présence OpenRoom réutilisée), panneau live + classement stub, events.
  - `/openroom` redirige vers `/lounge` (`?agent=` conservé). HQ / SiegeLifeLinks /
    nav outils / overview / manuel : vocabulaire « Agent Lounge ».
  - Phase 46 V1 (DEC-031). Suite : V2 `lounge_scores`.

## 2026-08-11 — Agent Lounge V0 contrat (docs)

- **Type :** docs
- **Details :**
  - Phase 46 V0 : `docs/specs/SPEC_AGENT_LOUNGE.md` + DEC-031 — OpenRoom/repas
    → Agent Lounge ; scores Lounge ≠ competition/trust ; reset mensuel ; idle
    filler ; propose→validation ; UI structure maquette / palette Hub.
  - `data/lounge_product.json` (scaffold) ferme la gate Academy
    `lounge_product_ready` ; runtime scores iront dans `lounge_scores.json`
    (gitignore). Suite : V1 shell `/lounge`.

## 2026-08-11 — Identité CEO : solopreneuse, pas « nomade » (docs/chore)

- **Type :** docs / chore
- **Details :**
  - Retrait du framing « Emilie nomade / vit en van » dans la vision R&D,
    `seed_knowledge`, leçons Mem0 (`inject_lessons`) et brand voice company.
  - Emilie = CEO solopreneuse ; NUAWAY reste un produit mobilité (audience OK),
    pas l’identité de toute ALNUA. Placeholders analytics génériques.
  - Relancer `python scripts/seed_knowledge.py` (+ `inject_lessons` si besoin)
    pour rafraîchir Mem0 si d’anciennes leçons lifestyle y sont encore.

## 2026-08-11 — Maquette CEO / Secrétariat / Direction (style)

- **Type :** style / feat
- **Details :**
  - Infrastructure visuelle command center (panneaux, anneaux, quick links)
    alignée maquette ; **palette ALNUA** (cuivre `#E09B6A`, obsidienne, ivoire,
    teal / danger).
  - Composants `web/src/components/siege/*` branchés sur `/ceo`, `/secretary`,
    `/hub` ; actions live (chat, dossiers, outils Nadia) conservées sous le
    dashboard.

## 2026-08-11 — ALNUA Desk (Spark) renomme Nadia Desktop (chore)

- **Type :** chore / brand
- **Details :**
  - Produit desktop : **ALNUA Desk** · tagline **Spark** ; persona chat = Nadia.
  - Lanceur `ALNUA Desk.bat` ; `Nadia Desktop.bat` = alias de compat.
  - Titre fenêtre / header UI / raccourcis Bureau mis à jour.

## 2026-08-11 — Nettoyage lanceurs Windows (chore)

- **Type :** chore / docs
- **Details :**
  - Racine : **4 `.bat` seulement** (`Installer` / `ALNUA Hub` / `Arreter` /
    `Nadia Desktop`) + `LIRE-MOI.txt`.
  - Doublons (ouvrir, relancer, réparer…) déplacés dans `scripts/windows/`.
  - Raccourcis Bureau limités à 3 ; purge des anciens noms confus.

## 2026-08-11 — Portraits all + CEO/Direction/Secrétariat redo (feat/style)

- **Type :** feat / style
- **Details :**
  - Portraits pour **tous** les agents (`public/agents/portraits` + sync) ;
    portraits IA pour Direction / Nadia / Solène / Clara + chefs de pôle.
  - Refonte `/ceo`, `/hub`, `/secretary` : void (plus de slabs gris), roster
    portraits, liens visibles **HQ · Repas & détente · Compétition**.
  - Page `/competition` ; OpenRoom = salle de repas ; nav outils mise à jour.
  - Nadia Desktop = **chat only** (plus d’éditeur) ; contrats Hub en **`.docx`**.
  - Pilules barre commande + X ALNUA réduites ; `Card` fond transparent.

## 2026-08-11 — H5 polish HQ immersif (feat)

- **Type :** feat
- **Details :**
  - `/hq` : carte interactive (hotspots `hq-hub-offices` + asset 17 bureaux) ;
    rail off-map (juridique, bibliothèque, IDE, admin).
  - Portraits clés : Nadia, Aria, Solène (`public/agents/portraits`).
  - OpenRoom = salle de repas & détente ; identity strips CEO/Secrétaire/Legal ;
    nav « Plan HQ ».

## 2026-08-11 — Bureau juridique Solène + version complète Nadia (feat)

- **Type :** feat
- **Details :**
  - **Bureau `/legal`** : persona Solène (skills, catchphrase, méthode) + panel
    avis/review/templates ; nav console / HQ off-map ; team `legal`.
  - **Docs Nadia** : `services/nadia_docs` + API `/nadia/docs*` (md + export txt/docx).
  - **Desktop v2** : fenêtre paned chat + éditeur ; boot logon lance l’UI.
  - **Housekeeper** Clara Nest — scan/propose/apply + quarantaine (DEC-030).
  - **Templates** enrichis (`contract_template_bodies`) ; research deep depuis Nadia.

## 2026-08-11 — Nadia NL réel + avocate entreprise + templates (feat)

- **Type :** feat
- **Details :**
  - **Lot A :** intent LLM Nadia (`secretary_intent_llm`) — paraphrases OK ;
    conversation = vraie assistante (plus de bot à mots magiques).
  - **Lot B :** agent `legal_counsel` (Solène Hariri) — avis / review / validate
    UE·USA·Asie ; endpoints `/agents/legal-counsel/*` ; escalation depuis Nadia.
  - **Lot C :** catalogue templates (`contract_templates_registry` + doc guide) ;
    `draft_contract` branché scaffolds ; disclaimer juridique.
  - Ménage PC (quarantaine) **reporté** — prochain lot.

## 2026-08-11 — H4 Nadia filtre + Aria stratégique (feat)

- **Type :** feat
- **Details :**
  - Routing Assistants : Academy / brief / mails → Nadia ; R&D / plans → Aria ;
    toggle Auto/Aria/Nadia visible dans le tiroir ; défauts bureau-aware.
  - Morning brief LLM **une seule fois** (cache passé au digest Nadia) ; bot
    Telegram Nadia ne double plus 8h si `SCHEDULER_LEADER=1`.
  - `/ceo` : brief du jour + dossiers pending + chat ; `/secretary` : chat Nadia
    + SAV ; bots Telegram via `assistant_chat`.
  - Tests `tests/test_assistant_router.py`.

## 2026-08-11 — H3 manuel in-app CEO + bibliothèque (feat/docs)

- **Type :** feat / docs
- **Details :**
  - Rendu Hub des guides `docs/*.md` via `/docs/[...slug]` + `docs-fs.ts`.
  - Carte **Manuel** sur `/ceo` et pin sur `/library` ; index `/docs` cliquable.
  - Route `ROUTES.userManual` → `/docs/guides/user-manual`.

## 2026-08-11 — H3 manuel utilisateur noob (docs)

- **Type :** docs
- **Details :**
  - `docs/guides/user-manual.md` — guide CEO (écrans, pôles, arbres/dossiers,
    quotidien, sécurité, dépannage).
  - Refresh `first-15-minutes.md` + `concepts.md` (launcher H1, `/health` sans
    `/v1`, tiroir Assistants, OpenRoom réel).
  - Liens : `docs/README.md`, `/docs` page, installation Suite.

## 2026-08-11 — Security Sentinel + launch silencieux (feat/ops)

- **Type :** feat / ops / docs
- **Details :**
  - **Hugo (security_sentinel)** : patrouille Hub (clé, allowlist, rafale auth,
    `.env` Git) + lockdown localhost optionnel (`SECURITY_AUTO_LOCKDOWN`) ;
    cron 30 min ; endpoints `/ops/security/*`. **≠ Sentry** (crashs apps).
  - **Launch pro** : `launch-hub-silent.vbs` — double-clic Bureau sans CMD
    permanente ; raccourci install pointe le VBS.
  - Docs : installation UX + `SECURITY_HARDENING.md` tableau Sentry vs Sentinel.

## 2026-08-11 — H2 sécurité béton + H1 launch Hub (feat/ops)

- **Type :** feat / ops / docs
- **Details :**
  - **H2 :** `services/hub_auth.py` — clés canal (`HUB_API_KEY_WEB|N8N|MCP|CURSOR`)
    + `HUB_IP_ALLOWLIST` ; coding agent shell = SEC-001 ; webhook secrétaire
    exempté ; docs auth corrigées ; `SECURITY_HARDENING.md` ; DEC-028.
  - **H1 :** `Installer ALNUA Hub.bat` + `scripts/install-hub.ps1` /
    `hub-status.ps1` ; messages launchers FR ; install guide noob.
  - Tests : **538** passed / 6 skipped.

## 2026-08-10 — UI chrome Hub (style)

- **Type :** style
- **Details :**
  - Tokens / `globals.css` + Tailwind ; console shell/sidebar/topbar ;
    dept-v2 header/sidebar/command-bar ; harmonisation App/Gaming/Robo/
    Marketing/R&D/Finances.

## 2026-08-10 — Phases 34 + 35 + autonomie profonde (feat)

- **Type :** feat
- **Details :**
  - **Phase 34 :** spent enveloppes (manuel + computed), `GET /finances/budget-alerts`,
    factures (due_date / filtres / overdue), fiscal `upcoming→due` auto.
  - **Phase 35 :** persona `brand` (Élise Mercier, comms_hub), Content Studio
    Review Brand + gate approved/published, design system enrichi kit + layout_tokens.
  - **Autonomie :** `autonomy_resolver` trust→level 0–3 ; posts → `content_validation` ;
    `GET /workflows/runs?waiting=a_verifier` + `approve-step` + carte CEO.
  - `budget_transfer` toujours hors scope (DEC-016).
  - Tests : **524** passed / 6 skipped.

## 2026-08-10 — Phase 34 Finance vue globale polish (feat)

- **Type :** feat
- **Details :**
  - Vue globale cockpit : KPI cards brand + transactions récentes ;
    charts finances alignés ; pas de métrique inventée.

## 2026-08-10 — Phase 21 Gaming probes restants (feat)

- **Type :** feat
- **Details :**
  - UE5.8 probes + agency pour environment / narrative / sound / qa_gaming ;
    canon lore + builds QA ; filtres cap `skill_ue58` ; endpoints gaming studio.

## 2026-08-10 — MCP PermissionGuard progressif (feat)

- **Type :** feat
- **Details :**
  - Interception MCP via `X-MCP-Agent` + carte route→capability ;
    middleware 403 ; packs `cursor`/`mcp_client` fail-closed ;
    `PERMISSION_GUARD_MCP_ENABLED` ; tests `test_mcp_permission_guard.py`.

## 2026-08-10 — Review Chain E2E dry-run 2 PR→staging (test)

- **Type :** test
- **Details :**
  - E2E dry-run : mission 2 branches → integrate → staging auto ;
    `mission_ship` workflow dry-run ; ctx `_review_chain` / `integrate_done`
    partagé entre steps.

## 2026-08-10 — PermissionGuard call-sites extension (feat)

- **Type :** feat
- **Details :**
  - Call-sites : `mail:send`, `github:pr:create/merge`, `git:commit` /
    `git:push:feature`, `workflow:abort` (missions + workflow runs) ;
  - Packs : `mail:send` pour `coo` + `system` ; API abort mission/workflow ;
  - Tests étendus `test_permission_guard.py`.

## 2026-08-10 — Phase 45 Context Engine AAF Phase F (feat)

- **Type :** feat
- **Details :**
  - Context Engine L1–L4 + promotion collective (DEC-027) ;
    spec `SPEC_CONTEXT_ENGINE.md`.
  - Wipe L4 fin de step ; `inject_learning_context` délégué ;
    API `/context/*` ; tests `test_context_engine.py`.

## 2026-08-10 — Phase 44 Capability Guard AAF Phase E (feat)

- **Type :** feat
- **Details :**
  - Capability Packs + PermissionGuard fail-closed (DEC-026) ;
    Trust Graph `trust_graph.jsonl` ; spec `SPEC_CAPABILITY_GUARD.md`.
  - Merge + ads:spend branchés ; API `/capabilities*`,
    `/permission-guard/check`, `/trust-graph/recent` ; UI décisions `/trust`.
  - Tests `tests/test_permission_guard.py`.

## 2026-08-10 — Phase 43 Review Chain AAF Phase D (feat)

- **Type :** feat
- **Details :**
  - Review Chain AUTO→BOARD→POLICY→INTEGRATE (`review_chain`, DEC-025) ;
    spec `SPEC_REVIEW_CHAIN.md`.
  - `merge_autonomy` (staging trust / main humain / academy auto) ;
    recipe `mission_ship` ; API `/review-chain/*` ; integrate Mission.
  - Tests `tests/test_review_chain.py`.

## 2026-08-10 — Phase 42 Loop Engine AAF Phase C (feat)

- **Type :** feat
- **Details :**
  - FSM execute→evaluate→feedback→retry (`loop_engine`, DEC-024) ;
    spec `SPEC_LOOP_ENGINE.md`.
  - `fix_pipeline` + `plan_executor` branchés ; workflow `RETRYABLE` vs
    `ECART` ; settings `LOOP_*` ; `GET /loop/defaults`.
  - Cap strict (`LOOP_STRICT_MAX_ITERATIONS`) sur merge / ship /
    integrator / fix_pipeline via `is_strict_loop` + `resolve_max_iterations`.
  - Tests `tests/test_loop_engine.py` (FSM, cap, feedback, workflow retry,
    strict ceiling).

## 2026-08-10 — Phase 41 Mission Graph AAF Phase B (feat)

- **Type :** feat
- **Details :**
  - Mission → Tasks DAG (`depends_on`) + store `data/missions/` (DEC-023) ;
    spec `SPEC_MISSION_GRAPH.md`.
  - API `/missions*` ; `run_coo_plan` passe par le graphe ; OpenRoom
    `missionId` ; client `missions-api.ts`.
  - Tests `tests/test_mission_graph.py` (parallèle, deps, fail→blocked).

## 2026-08-10 — Phase 40 agent isolation AAF Phase A (feat)

- **Type :** feat
- **Details :**
  - Resource locks + execution slots + merge policy (DEC-022) ;
    spec `SPEC_AGENT_ISOLATION.md`.
  - Câblé sur coding worktrees, `parallel_runner`, `plan_executor`,
    `fix_pipeline` ; API `/isolation/*` ; settings `ISOLATION_*`.
  - Tests `tests/test_agent_isolation.py` (collision paths, slots, merge deny).

## 2026-08-10 — HTTP dédié game_director / rnd_agent / coding_coach (feat)

- **Type :** feat
- **Details :**
  - `POST /agents/game-director/instruction` + lore search (offline-safe).
  - `POST /agents/rnd-agent/research|prototype|instruction`.
  - `POST /agents/coding-coach/teach|exercise|instruction` (+ registry pipeline).

## 2026-08-10 — Idle offline + preview livrables + promote tickets (feat)

- **Type :** feat
- **Details :**
  - L2 débloqué côté file du jour ; drain offline sans OpenRouter.
  - `IDLE_OFFLINE_MODE` + fallbacks L1 (templates / triage candidats).
  - API livrables + `POST /workflows/idle/promote-tickets` ; preview UI `/ceo`.

## 2026-08-10 — Idle suite : UI CEO + L1 LLM + load réel dept (feat)

- **Type :** feat
- **Details :**
  - `/ceo` : `CeoIdleQueueCard` (replan / valider L2 / drain).
  - L1 `company_draft` / `product_triage` → vrais drafts (Anouk skill /
    Sam PM), jamais publish.
  - Dept-v2 + missions : `resolveAgentLoad` / `agentLoadChip` (plus de %).

## 2026-08-10 — Phase 39 idle work MVP + P0 câblage (feat)

- **Type :** feat
- **Details :**
  - Recettes `idle_plan_day` / `idle_drain` + queue `data/idle_queue.json` ;
    scheduler + `GET/POST /workflows/idle/*` ; gates trust / CEO L2 / budget.
  - OpenRoom : `runId`/`taskId`/`progress` ; plus de load % cosmétique (0).
  - P0 : routes `dev_frontend`/`dev_integrator` ; cartes bureau R&D (6) ;
    Phase 21 probes UE/lore/builds sur 4 gaming ; `/analytics` → Layla/Axel.
  - Spec DEC-021 + tests `tests/test_idle_work.py`.

## 2026-08-10 — Spec idle agent work (docs)

- **Type :** docs
- **Details :**
  - Contrat CEO : ambition entreprise (C), file hybride COO/CEO, self-dev
    seulement si trust ≥ 70, budget LLM idle adaptatif (`cost_monitor`).
  - `docs/specs/SPEC_IDLE_AGENT_WORK.md` + DEC-021 + Phase 39 ROADMAP.
  - Lien croisé depuis `SPEC_WORKFLOW_ENGINE.md`.

## 2026-08-10 — Full debt paydown : zéro fichier >300 lignes (refactor)

- **Type :** refactor
- **Details :**
  - Suite du paydown repo-wide (pas seulement la dernière vague produit) :
    agents, services, routers, skills, bots, config — façades + siblings.
  - Parmi les gros : `rnd_ceo_agent`, hypothesis tree, telegram, playbooks,
    dispatch executor, orchestration, `advanced_services`, `agents_pole`,
    `agents/base` (LLMClient), `skill_gh_issues`, `skill_agent_learning`,
    `workflow_engine`, `settings`, nomenclature, brand/pipeline routers, etc.
  - APIs / routes / imports publics préservés via façades.
  - **0** fichiers Python >1000, **0** >500, **0** >300 sous
    `agents/` `services/` `api/` `skills/` `bots/` `config/` `database/`.

## 2026-08-10 — Full debt paydown : zéro fichier >1000 lignes (refactor)

- **Type :** refactor
- **Details :**
  - `skill_coding_agent` → cli/prompt/worktree/hub_aider/backends + façade.
  - `rnd_repository` → helpers + mixins ideas/dossiers/sections/assets/promote.
  - `core.py` vidé → `projects/tickets/robo_ops/gaming_ops/roadmap/posts/analytics/faq`
    (+ folds feedback/sav).
  - **0** fichiers Python >1000 lignes. Residual : ~24 >500 / ~70 >300.

## 2026-08-10 — Debt paydown + bible docs (refactor + docs)

- **Type :** refactor + docs
- **Details :**
  - Docs : racine → 8 fichiers vivants ; specs/guides/plans → `docs/` (bible
    `docs/README.md` + classeur).
  - `api/schemas.py` → façade + modules ≤300.
  - `api/routers/rnd.py` éclaté (`rnd_dossiers`, committee, assets, social, ceo,
    product) — tous ≤300.
  - Liens AGENTS / CLAUDE / rules / audit script mis à jour.

## 2026-08-10 — Vague F : hygiène anti-drift post A–E (docs)

- **Type :** docs / chore
- **Details :**
  - Resync comptes : **44** routers, **433** tests collectés, Next 16.3.0,
    Vitest 35, npm audit 0.
  - IMPLEMENTATION_STATUS / ROADMAP Phase 21–28–35 alignés sur A–E.
  - Entrée `DOC_AUDIT.md` Vague F (Audit 005 toujours ≤ 2026-08-30).
  - Purge check : vault library / brand_kits propres ; pas de split >300.

## 2026-08-10 — Vague E : R&D Explorer veille externe (feat)

- **Type :** feat
- **Details :**
  - `rnd_explorer` — scan HN/Reddit/GitHub + brief labo (Idris).
  - `GET /rnd/explorer/signals`, `POST /rnd/explorer/brief`.
  - Onglet Explorer sur `/rnd-v2` (seed → Pipeline).
  - Tests `test_rnd_explorer.py`.

## 2026-08-10 — Vague D : Brand design system (feat)

- **Type :** feat
- **Details :**
  - `brand_design_system` + voice `content_company` ; recipes Review Board.
  - Router `brand_system` : `GET /brand/design-system`, `POST /brand/review`.
  - Marketing Brand Center branché ; tests `test_brand_design_system.py`.
  - Hors scope : persona multi-room Brand, débat LLM.

## 2026-08-10 — Vague C : Finance cockpit forecast (feat)

- **Type :** feat
- **Details :**
  - `finance_cockpit_forecast` + `GET /finances/cockpit-forecast` /
    `POST /finances/forecast/llm` (Rémi + ledgers réels).
  - Onglet Budgets & Fiscal : stats, kind/échéance, spent, panneau forecast.
  - Tests `test_finance_cockpit_forecast.py`. `budget_transfer` toujours reporté.

## 2026-08-10 — Vague B : probes robotique Phase 21 (feat)

- **Type :** feat
- **Details :**
  - `skills/skill_robo_lab.py` — lab tests + builds (vide honnête).
  - Router `robo_phase21` : BOM mech/industrial, lab QA/safety/sim, Pi vision.
  - Console `/robo` : probes Vague B.
  - Tests `test_robo_phase21.py`.

## 2026-08-10 — DEC-020 : agency Gaming = Claude Code sur le PC (feat)

- **Type :** feat
- **Details :**
  - `skills/skill_gaming_agency.py` — Claude Code / coding pipeline sur
    `UE_PROJECT_PATH` (worktree) pour les agents studio.
  - Endpoints `GET/POST /gaming/studio/agency/*` + `POST /gaming/ue58/tools/call`.
  - Console Gaming : statut agency + formulaire « Lancer sur le PC ».
  - `CODING_AGENT_IDS` : + ai_programmer / technical_artist / vfx_artist.
  - DEC-020 : pas de computer-use GUI Windows total.

## 2026-08-09 — Vague A : pont Hub ↔ UE5.8 (feat)

- **Type :** feat
- **Details :**
  - `SPEC_UE58_BRIDGE.md` + `skills/skill_ue58.py` (health, caps filtrées, chat, GDD).
  - Router `ue58_bridge` : status, probes Kenji/Otto/Diego, chat, gdd/sync.
  - Console Gaming : badge Nwiro → statut UE5.8 via Hub.
  - Tests `test_ue58_bridge.py` ; Nwiro resté legacy.

## 2026-08-09 — P0 décisions : UE5.8, Pi, UI *-v2 (docs)

- **Type :** docs
- **Details :**
  - **DEC-017** — pont Gaming = serveur UE5.8 (chat + GDD + outils) ; Nwiro
    abandonné (DEC-009 superseded) ; Godot reste optionnel.
  - **DEC-018** — Eve Pi différé ; agents via Hub SSH ; WinSCP = humain.
  - **DEC-019** — Finance/Marketing restent `*-v2` ; stash BUG-019 jeté.
  - `budget_transfer` toujours reporté (note DEC-016).
  - `CLAUDE.md` + skill `/alnua-godot` + Phase 21 ROADMAP alignés.

## 2026-08-09 — BUG-004 : split specs / personas / rnd_center (refactor)

- **Type :** refactor
- **Details :**
  - `config/agent_specs_registry.py` et `config/agent_personas.py` → façades +
    modules par pôle (`agent_specs_*.py`, `personas_*.py`) — tous ≤300 lignes.
  - `agents/rnd_center.py` → façade + `rnd_center_{llm,store,observe,pipeline,library}.py`.
  - Tests `test_rnd_library_develop` patchent les modules d’implémentation.
  - BUG-004 fermé (hotspots) ; dette >300 ailleurs notée en backlog hygiène.
  - `ruff` + `pytest` 401 passed / 6 skipped.

## 2026-08-09 — Eve robotics : BOM IA (alternatives, montage, rôles) (feat)

- **Type :** feat
- **Details :**
  - `services/eve_sourcing.py` + endpoints electronics/mechanical/hardware ;
    `GET /robo/pi-bridge` (SSH agents, Pi plus tard OK ; WinSCP = fichiers manuels).
  - UI `/robo` : panneau BOM clair + Alternatives / Plan montage / Qui build quoi.
  - Clarifie : robot physique ≠ app compagnon (`dev_app` comme Naïa).
  - Tests `test_eve_sourcing.py`.

## 2026-08-09 — Vague 4 durabilité : purge orphans + habitudes (chore + docs)

- **Type :** chore + docs + test
- **Details :**
  - Untrack **338** notes vault library (hors `_index/`) + `brand_kits/migration-test`
    déjà gitignorés — plus de dumps dans git.
  - Supprime `skills/coding_facade.py` orphelin ; DEC-008 / BUG-015 mis à jour.
  - Checklist **Habitudes durabilité** dans `AGENTS.md` (audit ≤3 sem., purge,
    ratio tests, vault, worktrees).
  - Tests HTTP budgets/fiscal (`test_finance_budgets_api.py`) — ratio surface Vague 3.
  - Prochain audit santé planifié ≤ **2026-08-30** (après Audit 004).

## 2026-08-09 — Vague 3 produit derrière l'UI : Finance + Phase 21 + MVP honesty (feat)

- **Type :** feat + docs
- **Details :**
  - **3A Finance :** ledgers JSON budgets + fiscal_obligations ; API CRUD ;
    onglet « Budgets & Fiscal » ; `budget_transfer` **reporté** (pas stubbé).
  - **3B Phase 21 :** 3 skills — `ai_programmer`/Nwiro probe, `firmware`/Pi probe,
    `electronics`/`skill_bom` ; endpoints + tests.
  - **3C :** briefing COO lit `cross_dept` queue ; Review Board LLM derrière
    `REVIEW_BOARD_LLM` (off par défaut) ; ROADMAP sans MVP ambigu.
  - Vérifié : pytest ciblés + suite ; Vitest / tsc.

## 2026-08-09 — Vague 2 dette structurelle BUG-004 : MissionsTab + split COO (refactor)

- **Type :** refactor + docs
- **Details :**
  - **FE :** `DeptMissionsTab` partagé (`web/src/components/shared/dept-missions-tab.tsx`) ;
    wrappers fins app / gaming / robo (`*-v2/missions-tab.tsx`).
  - **COO :** `coo_agent.py` façade **~576** lignes (était ~1476) — modules
    `coo_constants` / `coo_intents` / `coo_routing` / `coo_composio_tools` /
    `coo_project` / `coo_briefing` / `coo_delegates` / `coo_plan` / `coo_handlers` ;
    re-exports compat (tests, telegram_ack, secretary).
  - **BUG-004** mis à jour (mitigé, pas fermé — specs_registry / personas / rnd_center).
  - Vérifié : ruff OK ; pytest **386** passed / 6 skipped ; Vitest **35**/35 ; `tsc` OK.

## 2026-08-09 — Vague 1 hygiène bloquante : Next 16 + Trust UI (feat + fix + docs)

- **Type :** feat + fix + docs
- **Details :**
  - **BUG-017 fermé :** Next **15.5.23 → 16.3.0**, eslint **9**, `eslint.config.mjs`
    (plus de `next lint`), override `dompurify@3.4.13` → `npm audit` **0** vulns.
  - **Phase 31 UI :** `/trust` + `AgentTrustView` + `trust-api` (bandes DEC-011) ;
    lien depuis `/hub` ; Vitest helpers.
  - Docs sync Next 16 (README / ARCHITECTURE / CLAUDE / TESTING / ROADMAP).
  - Vérifié : `tsc` / `eslint` / Vitest **35**/35 / `build:safe` verts.
  - Note : règles hooks React Compiler v6 nouvelles laissées `off` (dette lint
    progressive, pas un silence produit).

## 2026-08-09 — Vague 0 garde-fous code sain — clôture 100 % (docs + chore)

- **Type :** docs + chore
- **Details :** checklist fin de lot dans `AGENTS.md` ; `ALNUA_OVERVIEW.md` tracké ;
  Next 15 + `build:safe` dans `CLAUDE.md` ; prune `feat/rnd-dossier-hub` +
  `fix/auto…` ; **BUG-019 fermé** (WIP pole-dashboard stashé, HEAD `*-v2` live) ;
  DOC_AUDIT Vague 0 100 % ; working tree clean ; `main` sync `origin`.

## 2026-08-09 — Sprint REM-002 close-out analysis (docs)

- **Type :** docs
- **Sprint commit produit :** `7dfad6f` (Next 15 + workflow split + hub/analytics).
- **Details :** analyse 14 sections (code review + intégrité + gouvernance) —
  remédiation Audit 002 A–E + clean suite. Integrity : `tsc`/`eslint`/`build:safe`
  OK ; Vitest **33**/33 ; pytest **386** passed / 6 skipped (**392** collected) ;
  ruff OK. DoD remédiation ~**90%** (MVP Phases 30/31/32/36 assumé). Ouverture
  **BUG-019** (WIP local mockup `/finances`/`/marketing`). Voir `DOC_AUDIT.md`
  Sprint REM-002. Ouverts : BUG-004, BUG-017, BUG-019.

## 2026-08-09 — Audit 004 health check (docs)

- **Type :** docs
- **Details :** second health check 10 dimensions le même soir (post Next 15 /
  remédiation A–E). Verdict 🟢 Good (était 🟡 Concerning en Audit 002).
  BUG-018 ouvert+fermé (micro-drift Next 14 / comptes tests / ROADMAP).
  Resync README, ARCHITECTURE, TESTING, IMPLEMENTATION_STATUS, ROADMAP,
  BUGS stats. Canvas `project-health-audit-004-2026-08-09.canvas.tsx`.
  Ouverts restants : BUG-004, BUG-017.

## 2026-08-09 — Bugs + clean : Next 15, workflow split, FE tooling, hub/analytics live (fix + refactor)

- **BUG-004 :** `workflow_engine` découpé (dossier/ops/ship handlers, fichiers ≤300 sauf engine 447).
- **BUG-017 :** Next **15.5.23** (mitigation partielle ; reste 3 high → Next 16).
- FE : `tsc` 0 erreur ; Vitest 33/33 via `@vitejs/plugin-react-swc`.
- `/hub` + `/analytics` shells live (plus de mockup primary).
- **Build :** `next build` corrompu si `next dev` écrit `.next` en parallèle →
  `npm run build:safe` (`NEXT_DIST_DIR=.next-build`) ; lockfile racine vide retiré.

## 2026-08-09 — Clean suite : DeptV2 chrome + live CEO/Secretary/Brand (refactor + fix)

- Shared `DeptV2PageShell` on all `*-v2` pages (dead local header/sidebar removed).
- `/ceo` → `CeoCockpitPanel` ; `/secretary` → Nadia + console ; `/brand` déjà `BrandView`.
- Residual mockup : `/hub` + `/analytics` only. Vitest routes live étendu.

## 2026-08-09 — Audit 003 : vérification A–E + nettoyage docs/hygiène (docs + chore)

- Verdict : code Phases B–E conforme MVP ; docs ROADMAP/README/IMPLEMENTATION_STATUS
  resync (40 routers, Phases 30/31/32/36 MVP) ; tmp screenshots supprimés ;
  `tmp-mockup-refs/` gitignoré ; suppressions `skill_aider`/`skill_openhands` stagées.
- Tests rejoués : 29 pytest + 12 vitest + ruff OK.

## 2026-08-09 — Phase E remédiation : MVP Phases 30/31/32/36 (feat + test + docs)

- **Phase 30 :** recettes `content_validation` / `campaign_validation` + autonomie
  0–3 (`services/workflow_validation_recipes.py`) ; emit `workflow_step_completed`
  à chaque étape du moteur (DEC-012).
- **Phase 31 :** `services/agent_trust.py` + `GET /agents/trust` (DEC-011).
- **Phase 32 :** `config/quality_gates.py` + `services/review_board.py` +
  `POST /review-board/evaluate` (score structurel MVP, DEC-013).
- **Phase 36 :** handlers cross-dept → `data/cross_dept_queue.json` +
  `GET /cross-dept/queue`.
- Tests : `tests/test_phase_e_mvp.py` ; router `api/routers/trust.py` (40e).

## 2026-08-09 — Phase D remédiation : orphans, façades, split rnd_trees, aliases (refactor + docs)

- **Type :** refactor + docs + chore
- **Details :**
  - **BUG-014 :** suppression `skills/skill_aider.py` + `skills/skill_openhands.py`
    (jamais importés runtime). `brand_agent` **conservé** (Phase 35 / SPEC / tests).
  - **BUG-015 :** `skills/coding_facade.py` (entry Hub vs watchdog) ;
    `services/facades/briefing_facade.py` documente les 3 chemins briefing.
  - **BUG-004 (1er cut) :** routes arbres + benchmark extraites vers
    `api/routers/rnd_trees.py` (~158 lignes) ; `rnd.py` allégé ; **39** routers.
  - **BUG-005 :** aliases `rnd_*_agent` → ids courts ajoutés (`coo_agent` était
    déjà aliasé). MissionsTab partagé **reporté** (trop large pour ce lot).
  - DEC-008 addendum (Aider reste backend de `skill_coding_agent`).

## 2026-08-09 — Phase C remédiation : deps npm, vault policy, hygiène git (fix + chore + docs)

- **Type :** fix + chore + docs
- **Details :**
  - **BUG-012 :** `npm audit fix` + `vitest@4.1.10` (critical fermée) + `postcss@8.5.26`
    (+ overrides). Reste **8** vulns (0 critical, 5 high) — surtout Next 14.2.35,
    acceptées jusqu’à migration Next 15/16 (pas de `--force`).
  - **BUG-016 :** policy `vault/obsidian/library/_index/RETENTION.md` + gitignore des
    corps `library/**` (sauf `_index/`).
  - **BUG-002 :** `git rm --cached data/agent_models.json` (fichier local conservé).
  - **BUG-003 :** `fastapi-mcp==0.4.0` ajouté à `requirements.lock.txt` (venv).
  - Branches locales juin 2026 supprimées (`feat/issue-*`, `fix/auto…`).
    `feat/rnd-dossier-hub` conservée (active / remote).

## 2026-08-09 — Phase B remédiation : routes live + Finance factures (fix + feat)

- **Type :** fix + feat
- **Details :**
  - **BUG-013 :** `/finances`, `/marketing`, `/app`, `/gaming`, `/robo` ré-exportent
    leurs shells `*-v2` (plus de `MockupDepartmentPage` sur la nav primaire).
  - **`/rd` :** shell `rnd-v2` par défaut ; deep-links `?dossier=` / `?tab=` /
    `?tree=` / `?view=` restaurent `RdPageContent` (éditeur legacy).
  - **Finance DEC-016 UI :** onglet renommé « Coûts & Factures » (panel SaaS /
    factures / Revolut déjà branché) + KPI « Factures à payer » sur Vue globale.
  - Tests Vitest : `department-routes-live`, `finances-api` helpers.

## 2026-08-09 — Audit santé + catch-up gouvernance Phases 22-38 / Finance / Ops (docs + feat + ops)

- **Type :** docs + feat + ops + fix (catch-up rétroactif — le CHANGELOG avait
  décroché au 2026-07-31, voir BUG-011)
- **Commits clés :** `f1f6f7a` / `590f5f6` (ops Sentry + security-ingest Résonance),
  `f1a1224` (department v2 UI, finance SaaS, marketing funnel, R&D council —
  ~352 fichiers / +25k lignes), `6dc1b29` (nettoyage panels mockup marketing),
  `c84ec7d` (Audit 002 health check)
- **Details :**
  - **Phases 22-27 (R&D v2) :** coquille `/rnd-v2`, Innovation Pipeline, Incubateur
    Kanban, Moteur Conseil (réceptacle), Arbres mindmap, table Dossiers — marquées
    Complete dans `ROADMAP.md`.
  - **Phase 28 (Explorer veille) :** toujours ⏸️ Not started.
  - **Phases 29 / 33 / 37 (Marketing) :** Command Center visuel, Campagnes + Content
    Studio, mesure Reach/Engagement/ROI/Funnel — Complete ; funnel marketing API
    (`marketing_funnel`) dans le lot `f1a1224`.
  - **Phase 34 (Finance) :** 🔄 In progress — DEC-016 : ledger factures JSON, catalogue
    SaaS spend, Revolut lecture seule (API) ; UI `/finances-v2` et tables
    budgets/fiscalité encore en retard (Phase B du plan de remédiation).
  - **Phase 38 (harmonisation visuelle MockupShell) :** Complete côté rendu, avec
    caveat : routes primaires `/finances` `/marketing` `/rd` encore sur mockup —
    UI live sous `*-v2` (BUG-013, Phase B).
  - **Phases 30-32 / 35-36 :** toujours Not started (workflow validation recipes,
    Trust, Review Board, Brand transversal, event bus cross-dept) — bus
    `event_bus.py` existe déjà, wiring Phase 36 non fait.
  - **DEC-011–016 :** Trust séparé compétition, workflow générique unique, Review
    Board, stats Marketing manuelles, OpenRouter prompt cache, Comptabilité
    SaaS/factures/Revolut.
  - **Ops :** mapping Résonance dans Sentry hotfix + bug_watchdog ; security-ingest
    fortress alerts.
  - **BUG-009 / BUG-010 :** rate-limit authentifié + loader dossier R&D (corrigés
    fin juillet, absents du CHANGELOG jusqu’ici).
  - **Audit 002 (2026-08-09) :** verdict 🟡 Concerning — ouverture BUG-011…016 ;
    Phase A = ce catch-up gouvernance.

## 2026-07-31 — Roster Gaming/Robo, redesign UI départements, real-data Phases 15-20, fix Academy (feat + fix + chore)

- **Type :** feat + fix + chore
- **Commits :** `b071f5c` (roster 15 agents spécialisés Gaming/Robo, Phase 13),
  `7ff87a7` (redesign UI département — missions, backlog, docs, équipe, modules),
  `0b78386` (infra real-data builds/assets/télémétrie/communauté Gaming+Robo,
  Phases 15-20 + BUG-006/007/008), `b5fe7c3` (refresh export vault bibliothèque)
- **Details :**
  - **Phase 13 (agents) :** complète le roster App/Gaming/Robo avec les 15 rôles
    spécialisés déjà documentés dans `CLAUDE.md` (level designers, artistes,
    QA, safety, simulation) — endpoints MCP + specs opérationnelles inclus.
  - **Redesign UI départements :** nouveau shell (équipe/mission/chat), missions
    kanban + analytics, backlog, documentation, modules projet, déployé sur
    App/Gaming/Robo (`app-v2`/`gaming-v2`/`robo-v2`) + page détail projet. Détail
    complet dans `PLAN_DEPARTMENTS_UI_REDESIGN.md`/`TEST_PLAN_DEPARTMENTS_UI_REDESIGN.md`,
    suivis différés dans `TODOS.md`.
  - **Phases 15-20 (ROADMAP.md) :** remplace les données mock de builds/assets/
    labo/télémétrie/communauté Gaming+Robo par de vraies tables Supabase +
    endpoints + scripts rapporteurs + rendu réel, avec réceptacle honnête
    (pas de fake data) là où l'infra externe manque réellement (pipeline UE5,
    Steam Wishlist API, accès physique au robot Eve).
  - **BUG-006 :** connexions Supabase HTTP/2 périmées jamais retentées.
  - **BUG-007 :** dérive schéma `roadmap` (CHECK priority/status, colonnes
    `updated_at`/`linked_ticket_id` absentes) qui cassait silencieusement
    `POST /roadmap` et `/roadmap/from-ticket/{id}`.
  - **BUG-008 :** `agent_wake.py::get_pipeline_status()` annonçait le pipeline
    Academy "en cours" sur la seule base des labels GitHub, sans vérifier que
    le clone local existe — corrigé, puis le repo `alnua-academy` a été cloné
    dans `C:\Dev\alnua-academy` et les 5 issues bloquées relancées.
  - **Fix UI (non commité séparément) :** carte "Mission en cours" (Théo,
    `app-v2/team.tsx`) plafonnée + scrollable — un message d'erreur long
    (ex. `OpenRouter 402`) faisait exploser toute la rangée équipe.

## 2026-07-25 — Gouvernance, audit sécurité/qualité, méthode de travail (docs + fix)

- **Type :** docs + fix
- **Details :**
  - Bootstrap gouvernance : création de `ARCHITECTURE.md`, `ROADMAP.md`,
    `DECISIONS.md`, `BUGS.md`, `CHANGELOG.md` (ce fichier), `IMPLEMENTATION_STATUS.md`,
    `TESTING.md`, `DOC_AUDIT.md` — ALNUA Hub était le seul des 4 projets du workspace
    `C:\Dev` sans cette couche.
  - Audit sécurité + qualité de code (2 agents en parallèle) : correctifs SEC-001
    (injection shell critique sur `/ide/run`), SEC-004/005/006 (sanitization manquante
    sur `/sav/ask`, `/agents/brainstorm*`, `trend_monitor`), BUG-001 (violations
    `AgentBase.__init__`).
  - Décisions tranchées par Emilie : SEC-002/DEC-010 (`HUB_API_KEY` obligatoire dans
    tous les environnements, plus de mode dev ouvert) et DEC-009 (Nwiro/UE5 confirmé
    comme choix assumé, règle "Pas d'UE5" retirée de `CLAUDE.md`).
  - Méthode de travail agents IA : `AGENTS.md` (point d'entrée universel) +
    `.cursor/rules/agent-orchestration.mdc`, `ai-agent-survival.mdc`, `async-jobs.mdc`.
  - Suite complète (`pytest tests/ -q`) et `ruff` vérifiés verts après chaque étape.
    Détail complet dans `DOC_AUDIT.md` (Audit 001 + addendum).

## 2026-07-24 — Coûts & jalons (feat + fix)

- **Type :** feat + fix
- **Commits :** `013a04e`, `a3d33e2`, `8113af3`, `2ec99d2`, `3401e34`, `aa7b39d`, `8b366a5`
- **Details :** suivi combiné des coûts API (ElevenLabs auto + hosting manuel) sur la
  page Comptabilité ; "Jalons à venir" branché sur Google Calendar via Nadia ; fixes
  UI R&D (scroll, flexbox) ; vérification `library` corrigée pour checker la leçon
  apprise réelle plutôt que la seule source.

## 2026-07-23 — Centre R&D dossier hub + polish design (feat + fix + style)

- **Type :** feat + fix + style + chore
- **Commits :** `16c84c2`, `cbb9169`, `fd769c2`, `7f8061c`, `1a9d96f`, `c42e81f`,
  `7ae0798`, `617ab07`, `ddb979e`, `4dec459`, `ab36242`, `2ff02dc`, `7fcd614`,
  `d9880cd`, `b2e7a19`, `de90d83`, `8b05cd7`
- **Details :** complétion du pipeline Centre R&D dossier hub + extensions
  plateforme ; correctifs findings design (FINDING-001 à 006 : topbar, sparklines,
  hydratation SSR, contraste) ; retrait CreatorFlow/NUAWAY ops/media pipeline studio ;
  lint F401 enforced en CI ; noms d'agents réels dans le graphe de comm.

## 2026-07-23 — Audits P0/P1/P2 (fix)

- **Type :** fix
- **Commits :** `4b8f984` (P0 — agents R&D, montage routers), `e1a4f38` (P1 — auth
  bots, sanitizing input, résilience LLM, lint), `84e5664` (P2 — error boundaries web,
  routes comme source de vérité, couverture e2e), `5497218` (écarts restants —
  migrations, imports routers, openroom, pi-command)
- **Details :** série d'audits internes successifs fermant des écarts de sécurité et
  de robustesse identifiés en amont.

## 2026-06-24 — Migration 9-layer operating specs (feat)

- **Type :** feat
- **Commit :** `1a46408`
- **Details :** tous les personas migrés d'un `SYSTEM_PROMPT` 5-sections inline vers
  génération via `config/agent_operating_spec.py::get_system_prompt()`.

## 2026-06-13 → 2026-06-15 — Extension API + Centre R&D + assainissement (feat)

- **Type :** feat + chore
- **Commits :** `5c0447a` (Centre R&D dossier pipeline phases 0-8), `02fdba3`
  (extension architecture API Hub, services avancés au runtime), `10989d3`
  (assainissement Hub phases 0-6, perf lobby-bureau, extensions plateforme)

## 2026-06-12 — Durcissement sécurité + fallbacks robustesse (feat + fix)

- **Type :** feat + fix
- **Commits :** `7c86370` (X-Hub-Key obligatoire sur routes Hub API), `2df9669` (RLS
  anon restreinte à SELECT sur tables sensibles), `d094203` (restriction `/brand/assets`
  au dossier `brand_kits`), `cf9e9f9`/`f9054d0`/`831c2bf`/`c890f778`/`4656289`
  (fallbacks gracieux : Composio, Discord, Nwiro/UE5, SSH embedded, hardware BOM),
  `0cd7c53` (fix tests Windows + COO API), `41790b3`, `716767a`, `7c41e94`,
  `824a0ab`, `137a752`

## 2026-06-11 — Fondation du Hub (feat)

- **Type :** feat (burst initial)
- **Commits :** `e995186` (first commit) → `137a752`
- **Details :** mise en place initiale — API FastAPI, agents CrewAI, dashboard v3
  (siège social virtuel : lobby + bureaux par département), OpenRoom (war room
  visuelle), intégrations Mem0 (mémoire persistante), Langfuse (tracing LLM),
  Composio (OAuth gateway), Chroma (base de connaissances), OpenHands + Aider
  (pipeline codage autonome), skill Nwiro (UE5, port 5353 — choix confirmé assumé le
  2026-07-25, voir `DECISIONS.md` DEC-009).
