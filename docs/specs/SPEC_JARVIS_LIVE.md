# SPEC — Jarvis Live (voix temps réel + tâches asynchrones)

> Contrat produit Lot 0. Complète `SPEC_JARVIS_OVERLAY.md` (DEC-033), ne la remplace pas.
>
> **Statut :** Lots 1–5 implémentés (Phase 50). OAuth Instagram encore à valider chez Meta.
> **Décision :** DEC-038, DEC-039.
> **Source d'inspiration :** vidéo de Thomas Berton, « J'ai créé mon propre JARVIS avec
> Claude Code » (`youtube.com/watch?v=L0Xf2CyZur0`). Analyse faite sur la transcription
> et la description uniquement : le template de l'auteur n'est pas public, rien n'en a
> été copié.

---

## 1. Objectif

Emilie parle au Hub, **sans clavier**, et peut enchaîner plusieurs demandes sans attendre
la fin de la précédente. Chaque demande devient une **tâche en arrière-plan** exécutée par
un agent du Hub. Les tâches et leurs résultats s'affichent à l'écran. Quand une tâche se
termine, Jarvis le dit à voix haute en une ou deux phrases.

```
Emilie (voix)
   │  WebRTC (jeton éphémère délivré par le Hub)
   ▼
Modèle vocal temps réel ── outils: start_task / list_tasks / get_task_status / cancel_task
   │  appels d'outils exécutés par le navigateur
   ▼
Hub API  /live/*  ──►  Registre de tâches  ──►  agents du Hub (Aria, Nadia, dev…)
   ▲                         │
   │  SSE (mises à jour)     └─► event_bus ──► panneau d'écran + réplique vocale
```

Le modèle vocal est **un manager** : il comprend, délègue, résume. Il n'exécute rien lui-même.

## 2. Ce qu'on reprend de la vidéo

| Idée | Reprise |
|---|---|
| Voix vers voix en temps réel, interruption possible | Oui |
| Modèle vocal = manager qui délègue | Oui |
| Tâches en fond, plusieurs en même temps | Oui |
| Panneau de tâches + affichage des résultats à l'écran | Oui |
| Résumé parlé à la fin de chaque tâche | Oui |
| Contexte de conversation transmis aux tâches | Oui |

## 3. Ce qu'on ne reprend pas

| Idée de la vidéo | Pourquoi pas | Remplacement |
|---|---|---|
| Claude Code en `--dangerously-skip-permissions` sur le PC | Interdit par `ai-agent-survival.mdc` hors environnement isolé | Agents du Hub aux permissions bornées (`PermissionGuard`, Phase 44) |
| Publication LinkedIn directe sur ordre vocal | Action externe irréversible | Brouillon + **validation humaine** (voir 6.3) |
| Ouvrir n'importe quelle appli sur n'importe quel écran | Invariant « pas de computer-use GUI Windows total sans nouvelle DEC » | Hors scope, Lot 5 conditionné à une DEC séparée |
| Le nom et le personnage « Jarvis » | Demande d'Emilie (2026-10-04) : même système, mais **c'est Nadia** | Persona par défaut = Nadia (voix, nom affiché, ton). Aria reste possible plus tard, jamais fusionnée |

## 4. Décisions de cadrage (2026-10-04)

| Axe | Décision |
|---|---|
| Moteur vocal | API Realtime d'OpenAI, côté navigateur en WebRTC |
| Surface | Page du Hub web (`/live`), pas ALNUA Desk. Le Hub s'ouvre sur `/` (Command Center). Spark figé (DEC-041). |
| Exécutants | Agents du Hub existants. Pas de Claude Code lancé depuis la voix |
| Voix / faits | Reste la règle DEC-033 : **faits à l'écran, réplique en voix**, jamais l'inverse |
| Persona | **Nadia** partout dans l'interface (« Jarvis » n'apparaît nulle part) |
| Parité | Même interface et mêmes fonctions que la vidéo, voir §14 et §15 |
| Flag | `LIVE_VOICE_ENABLED=0` par défaut |
| Échec voix | Les tâches et le panneau fonctionnent sans la voix. Une panne Realtime ne casse jamais une tâche |
| Langue | Français, tutoiement |

## 5. Registre de tâches (cœur du système, utilisable sans voix)

Une tâche a : `id`, `agent_id`, `instruction`, `status`, `created_at`, `started_at`,
`finished_at`, `result` (texte), `artifacts` (liste de chemins), `file_ids` (pièces jointes
Hub Files, DEC-040), `error`, `session_id`.

États : `queued` → `running` → `done` | `failed` | `cancelled`.

Règles :

1. **Persistance** dans `data/live_tasks.json` (comme `agent_scores.json` : créé
   automatiquement, git-ignoré). Au redémarrage du Hub, les tâches `queued` et `running`
   passent en `failed` avec l'erreur `interrupted_by_restart` (le pool de workers est en
   mémoire : elles ne peuvent plus tourner). Elles ne sont jamais relancées
   silencieusement. Un fichier corrompu est mis de côté (`.corrupt.json`) et ne bloque
   pas le Hub. 200 tâches maximum conservées, les plus anciennes terminées partent d'abord.
2. **Concurrence plafonnée** par `LIVE_TASK_MAX_CONCURRENT` (défaut 3). Au-delà, `queued`.
3. **`done` seulement après vérification de l'état réel** : résultat non vide, et chaque
   artefact déclaré existe sur disque (`async-jobs.mdc`, « revérifier avant d'agir »). Le
   « j'ai fini » de l'agent n'est pas la preuve.
4. **Exécution** : trois exécutants, sans troisième moteur. `coo` et `secretary` passent
   par le point d'entrée du chat Hub (`assistant_chat`). `plan` passe par
   `services/plan_executor.py::run_coo_plan` : le COO décompose l'objectif et fait
   travailler les autres agents (analyst_data, content, etc.). Les agents spécialisés
   ne sont donc pas appelés directement par la voix, ils le sont via `plan`.
5. **Allowlist** (`LIVE_TASK_AGENTS`, défaut `coo,secretary,plan`) : le modèle vocal ne
   peut déclencher que ces exécutants. Une valeur inconnue dans la variable est ignorée.
6. **Événements** : chaque changement d'état fait `event_bus.emit("live_task_updated", …)`.
7. **Coût** : chaque appel LLM d'une tâche est suivi par `cost_monitor` comme aujourd'hui.

## 6. Sécurité

### 6.1 Entrées non fiables

La transcription vocale et tout contenu récupéré par une tâche (recherche web, emails)
sont du **contenu, jamais des instructions**. `instruction` passe par
`services/input_sanitizer.py::sanitize_user_input` côté router avant d'entrer dans un
prompt (règle `ai-agent-survival.mdc`, précédent SEC-006).

### 6.2 Clé OpenAI

La clé reste côté Hub. Le navigateur reçoit un **jeton éphémère** minté par
`POST /live/session`, avec durée de vie courte. La clé n'apparaît jamais dans le code web,
les logs ou une réponse API.

### 6.3 Actions externes = confirmation humaine

Envoyer un email, publier sur un réseau, payer, supprimer : la tâche produit un
**brouillon** affiché avec un bouton « Valider » à l'écran. Jarvis dit « Brouillon prêt,
tu valides ? » (gold 4.2 de la spec overlay). Aucune action externe ne part sur le seul
ordre vocal.

État au Lot 1 : Nadia garde sa propre barrière (`detect_send_confirm` : l'envoi d'un mail
n'a lieu que sur une confirmation explicite, dans la même `session_id`). Le champ
`needs_confirmation` et le bouton « Valider » sont reportés (dès qu'un exécutant
produit un brouillon) ; il faudra alors vérifier que `plan` ne contourne pas cette barrière.

### 6.4 Accès à l'API

Les endpoints `/live/*` sont protégés par `X-Hub-Key` comme le reste de l'API (DEC-010,
SEC-002). Le front les appelle uniquement via `web/src/lib/live-api.ts`, par le proxy
Next.js `/api/hub/[...path]` qui ajoute `X-Hub-Key` côté serveur : la clé n'arrive jamais
dans le navigateur, et `EventSource` fonctionne donc sans en-tête. Le flux SSE répond
avec `Cache-Control: no-cache, no-transform` : sans `no-transform`, le proxy compresse
le flux et livre les petites trames en retard (constaté : une tâche n'apparaissait qu'une
fois terminée).

## 7. Coût et garde-fous

- Micro en **écoute continue** (détection de parole côté OpenAI), choix d'Emilie du 2026-10-05 : pas de bouton à maintenir. Contreparties : bouton « Couper le micro », annulation d'écho du navigateur, et casque conseillé (haut-parleurs + micro = Nadia peut s'entendre et s'interrompre).
- Déconnexion automatique après 90 s sans échange (fait, côté navigateur, constante `IDLE_LIMIT_MS`).
- Plafond `LIVE_VOICE_MAX_MINUTES_PER_DAY` (défaut 30) ; au-delà, `POST /live/session`
  renvoie 429 et la page propose le mode texte.
- Chaque minute d'audio est enregistrée via `cost_monitor`.
- Tarif audio : **aucun prix n'est codé**. Chaque session clôturée est enregistrée dans
  `cost_monitor` avec `native_cost_usd=0` et `note=seconds=N`, plus le compteur quotidien
  `data/live_voice_usage.json`. [À COMPLÉTER : recopier le tarif officiel Realtime ici
  quand on voudra afficher un vrai dollar — ne pas inventer un prix.]

## 8. Voix et répliques

Réutilise les règles de `SPEC_JARVIS_OVERLAY.md` §3 : une réplique de 200 caractères
maximum, qui **ne relit pas** emails, numéros, heures en liste, JSON, URLs. Le persona
choisi (Nadia ou Aria) fixe le ton des instructions de session. Les fichiers de persona ne
sont pas modifiés ; le ton est porté par les instructions de session du modèle vocal.

À la fin d'une tâche, le navigateur injecte dans la conversation un message
« tâche terminée + résumé court » et demande une réponse vocale. Si la tâche est
`failed`, la réplique l'annonce sobrement, sans plaisanterie (règle Aria).

## 9. Lots

| Lot | Contenu | Dépend de |
|---|---|---|
| **0** | Cette spec + DEC-038 + ligne ROADMAP | – |
| **1** | Registre de tâches + `/live/tasks` (CRUD + SSE) + tests. Sans voix | Lot 0 |
| **2** ✅ | Cockpit Nadia (§14) : page Hub web avec panneau de tâches, écrans de résultats. Utilisable au clavier. Bouton Valider reporté (voir §13 bis) | Lot 1 |
| **3** ✅ | `POST /live/session` (jeton éphémère) + session WebRTC en écoute continue + outils `start_task` / `list_tasks` / `get_task_status` / `cancel_task` | Lot 2 |
| **4** ✅ | Réplique vocale à la fin des tâches, plafond de coût (`LIVE_VOICE_MAX_MINUTES_PER_DAY`), suivi `cost_monitor` (durée, tarif audio = 0 en attendant la page de prix). Écoute continue, interruption et inactivité 90 s déjà faites au Lot 3 | Lot 3 |
| **5** ✅ | Actions PC en allowlist (`open_url`, `open_app`, `open_file`) | DEC-039 |

### Fichiers impactés (prévision, à confirmer en début de chaque lot)

| Lot | Nouveau | Modifié |
|---|---|---|
| 1 ✅ | `services/live_tasks.py`, `services/live_tasks_store.py`, `services/live_tasks_stream.py`, `api/routers/live_tasks.py`, `tests/test_live_tasks.py` | `api/routers/__init__.py`, `config/settings_fields_hub.py`, `.env.example`, `.gitignore` |
| 2 ✅ | `web/src/app/live/page.tsx`, `web/src/components/live/*`, `web/src/lib/live-api.ts`, `live-cards.ts`, `web/src/store/live-store.ts`, `web/src/hooks/use-live-stream.ts`, `tests/test_live_tasks_api.py`, `tests/live_tasks_fixtures.py` | `web/src/lib/routes.ts`, `web/src/app/secretary/page.tsx` |
| 3 ✅ | `services/live_session.py`, `api/routers/live_session.py`, `web/src/lib/live-realtime.ts`, `live-voice-tools.ts`, `web/src/hooks/use-live-voice.ts`, `web/src/components/live/live-voice-controls.tsx`, `tests/test_live_session.py`, `web/src/__tests__/live-voice.test.ts` | `config/settings_fields_hub.py`, `.env.example`, `api/routers/__init__.py`, `live-api.ts`, `nadia-orb.tsx`, `live-cockpit.tsx` |
| 5 ✅ | `services/live_pc_actions.py`, `services/live_web_brief.py`, `config/settings_fields_live.py`, `tests/test_live_pc_actions.py`, `tests/test_live_web_brief.py` | `live_tasks.py`, `live_session.py`, `secretary_*`, `live-access-panel.tsx`, `live-work.ts` |

Chaque fichier reste sous ~300 lignes ; scinder avant d'y arriver.

## 10. Hors scope

- Ouverture d'applications hors liste blanche, clic, frappe, capture d'écran
- Claude Code lancé par la voix
- Clone de voix « Jarvis » de film
- Fusion Nadia + Aria
- Téléphonie

## 11. Points levés au Lot 3

- Endpoint et modèle (documentation OpenAI relue le 2026-10-04) : jeton via
  `POST https://api.openai.com/v1/realtime/client_secrets`, échange SDP du navigateur via
  `POST https://api.openai.com/v1/realtime/calls`, modèle par défaut `gpt-realtime`
  (réglable par `LIVE_VOICE_MODEL`, car les noms évoluent : `gpt-realtime-1.5`, `-2` existent).
- `OPENAI_API_KEY` est déclarée dans `config/settings_fields_hub.py` (vide par défaut) ;
  elle sert uniquement à créer les jetons.
- Auth du navigateur : proxy Next.js `/api/hub/*` (voir §6.4), via `hubFetch`.
- [À COMPLÉTER : noms exacts des événements serveur `response.output_audio_transcript.done`,
  `output_audio_buffer.started/stopped` et `response.done` (appels d'outils). Écrits d'après
  la documentation et les tests unitaires, **pas vérifiés avec une vraie session** : aucune
  clé OpenAI n'a servi pendant le développement. À confirmer au premier essai réel.]

## 12. Done Lot 0

- [x] Analyse de la vidéo et écarts avec ALNUA
- [x] Décisions de cadrage (voix, surface, exécutants)
- [x] Risques de sécurité identifiés (6.1 à 6.4)
- [x] DEC-038 enregistrée
- [x] Phase 50 dans `ROADMAP.md`

## 13. Done Lot 1

- [x] Registre persistant (`live_tasks_store.py`), reprise après redémarrage sans relance
- [x] Création, liste, lecture, annulation : `POST/GET /live/tasks`, `GET /live/tasks/{id}`, `POST /live/tasks/{id}/cancel`, `GET /live/agents`
- [x] Flux SSE `GET /live/tasks/stream` (instantané puis changements, heartbeat 15 s)
- [x] Allowlist `LIVE_TASK_AGENTS`, concurrence `LIVE_TASK_MAX_CONCURRENT`
- [x] `done` seulement si résultat non vide et artefacts présents
- [x] Annulation d'une tâche en cours : résultat tardif écarté
- [x] 22 tests (`tests/test_live_tasks.py`) ; suite complète 735 passés, ruff 0

## 13 bis. Done Lot 2 (cockpit, version sans voix)

- [x] Page `/live` (lien depuis `/secretary`), flux SSE reconnecté automatiquement, indicateur « Hors ligne — reconnexion… »
- [x] Panneau de tâches : statut, agent, durée qui s'incrémente, annulation
- [x] Cartes de résultat typées (texte, étapes d'un plan, erreur), rendues en texte React, jamais en HTML
- [x] « Tout effacer » vide les écrans sans toucher aux tâches
- [x] Repli clavier : choix Nadia / Aria / Équipe + champ de demande
- [x] Vérifié dans le navigateur : création, mises à jour en direct (~0,8 s), échec, rechargement
- [x] 16 tests web (suite 58), 23 tests Python (`test_live_tasks.py`, `test_live_tasks_api.py`) ; suite complète 736 passés, ruff 0, tsc 0, eslint 0
- Reporté : bouton « Valider » et `needs_confirmation` (aucun exécutant ne produit encore de brouillon) ; cartes liste/tableau/graphique/image ; transcription (Lot 3)

## 13 ter. Done Lot 3 (session vocale)

- [x] `POST /live/session` : crée un jeton éphémère OpenAI (TTL `LIVE_VOICE_SECRET_TTL_SECONDS`, 120 s). Désactivé par défaut (`LIVE_VOICE_ENABLED=0`) ; 503 si désactivé ou clé absente, 502 si OpenAI échoue, 429 au-delà de la limite. La clé OpenAI n'est jamais renvoyée ni journalisée
- [x] Instructions et outils fixés côté serveur (le navigateur ne peut pas les élargir) ; l'enum des agents suit `LIVE_TASK_AGENTS`
- [x] Personas Nadia (voix `marin`) et Aria (voix `cedar`), choisis avant la connexion
- [x] WebRTC mains libres : micro ouvert pendant la session, tours détectés par `server_vad` (créer la réponse + interrompre si l'utilisateur reparle) ; bouton « Couper le micro » ; filtre d'écho/bruit du navigateur et `noise_reduction: far_field`; fermeture automatique après 90 s sans échange
- [x] Outils → `/live/tasks` : `start_task`, `list_tasks`, `get_task_status`, `cancel_task` ; erreurs renvoyées au modèle sans exception ; résultats tronqués à 600 caractères et présentés comme des données
- [x] Le jeton n'est envoyé qu'à `https://api.openai.com` (contrôle côté navigateur)
- [x] Transcription affichée (ce que Nadia a entendu et dit), halo de l'orbe qui suit l'état réel (écoute / réfléchit / parle)
- [x] Micro libéré à la déconnexion, à la fermeture de la page et sur échec de connexion
- [x] 8 tests Python (`test_live_session.py`), 14 tests web (`live-voice.test.ts`)
- Vérifié dans le navigateur contre le vrai Hub : voix désactivée → message clair, bouton rétabli
- **Non vérifié** : une conversation réelle avec OpenAI (pas de clé). Voir §11

## 13 quater. Done Lot 4 (réplique + plafond)

- [x] Plafond `LIVE_VOICE_MAX_MINUTES_PER_DAY` (défaut 30) : `POST /live/session` répond 429 au-delà, le cockpit propose le clavier
- [x] Durée mesurée depuis le mint du jeton ; le navigateur signale la fin (`POST /live/session/end`) mais ne peut pas déclarer plus que l'horloge du Hub ; une session oubliée (onglet fermé) est facturée 5 min au prochain mint
- [x] `GET /live/usage` + affichage « N min de voix restantes aujourd'hui » ; fermeture auto quand le reliquat est épuisé
- [x] `cost_monitor` : une ligne `live_voice` / `realtime` par session, coût 0 (tarif inconnu)
- [x] Fin de tâche : Nadia commente à voix haute (note système + `response.create`) ; un échec est annoncé sobrement ; les tâches déjà terminées au chargement ne sont pas relues ; on n'interrompt pas l'utilisateur s'il parle
- [x] 6 tests Python (`test_live_voice_usage.py`) + 4 tests web (`live-voice-reply.test.ts`) ; suite 750 Python, 76 web

## 13 quinquies. Accès + cartes (2026-10-05)

- [x] `GET /live/access` : internet réel + état Composio Gmail/Agenda/Discord/Instagram
- [x] `POST /live/connect/{app}` allowlist + bandeau Connecter sur `/live`
- [x] Cartes résumé et graphique (données structurées, jamais du HTML agent)
- À faire côté humain : valider les liens OAuth dans le navigateur (Gmail, Discord, Instagram)

## 13 sexies. Done Lot 5 (PC allowlist + brief web, 2026-10-06)

- [x] `open_url` HTTPS + domaines `LIVE_PC_ALLOWED_DOMAINS` ; clés `LIVE_PC_ALLOWED_APPS`
- [x] Flag `LIVE_PC_ACTIONS_ENABLED` (défaut 0) ; pas de clic, pas de frappe, pas de `shell=True`
- [x] Recherche internet : brief avec sources à l'écran (`live_web_brief` + `live_web_search`, budget 10 s ; pas de pipeline R&D sur session Live)
- [x] Instagram OAuth : fallback `instagram_business` + hint Meta (compte Professionnel + Page Facebook)
- Hors scope inchangé : computer-use GUI, commande libre, publication irréversible

## 14. Cockpit Nadia (l'interface)

Reprend ce que la vidéo montre à l'écran, avec Nadia à la place de Jarvis. Les éléments
viennent de la transcription et de la démo décrite ; la mise en page exacte reste à
caler sur des captures d'écran (voir §16).

| Zone | Contenu |
|---|---|
| Bouton de session | Un grand bouton central : lancer / couper la session vocale. Un seul geste, comme dans la vidéo |
| État de Nadia | Écoute, réfléchit, parle. Un indicateur animé qui suit l'état réel de la session |
| Panneau de tâches | En haut à gauche : tâches en cours et terminées, avec agent, durée, statut, bouton annuler |
| Écrans de résultats | Zone principale : une carte par résultat, empilables. Types : texte, liste (ex. programme du jour), tableau, graphique, image, lien |
| Brouillons | Carte avec bouton « Valider » (post, mail) tant que rien n'est parti |
| « Tout effacer » | Commande vocale et bouton : vide les écrans sans toucher aux tâches |
| Transcription | Ligne discrète de ce que Nadia a entendu et dit, pour contrôler la compréhension |
| Repli clavier | Un champ texte : tout marche aussi sans micro |

Règle de contenu : les faits vivent dans les écrans, la voix ne fait que commenter
(DEC-033). Un résultat est une **donnée structurée** (`kind` + contenu), jamais du HTML
fourni par un agent : le front choisit le rendu, ce qui évite d'injecter du contenu
externe dans la page.

## 15. Parité fonctionnelle avec la démo

| Fonction de la démo | Aujourd'hui dans ALNUA | Ce qu'il reste à faire |
|---|---|---|
| Veille / actualité IA sur 7 jours | Oui (brief web + sources à l'écran, archive bibliothèque) | Enrichir la carte liste |
| Ouvrir Discord, mails, Instagram sur tel écran | Oui — allowlist + « sur l'écran 2 » / gauche / droite (DEC-044) | — |
| Programme du jour | Oui — carte liste | — |
| Résumé des emails | Oui — carte liste | — |
| Question sur la source d'une info | Oui — derniers résultats Live injectés dans la tâche (`live_session_context`) | — |
| Post LinkedIn dans mon style | Oui — Sofia (`content`) + voix marque, brouillon + Valider | — |
| Programmer pour une date, après vérification de l'agenda | Oui — créneaux libres + planifie + date | — |
| Image de presse libre de droits | Oui — Wikimedia + crédit | — |
| Générer une image | Oui — OpenRouter Images (`LIVE_IMAGE_MODEL`) | — |
| Graphiques à l'écran | Oui (carte `chart` + recharts ; Nadia sort un bloc ```chart) | Enrichir les séries (multi-courbes) |
| Créer une petite appli HTML et l'ouvrir | Oui — templates Hub (`data/live_html/`) + ouverture navigateur | Apps libres hors templates : plus tard |
| Tout effacer à l'écran | Oui — bouton, clavier, voix (`clear_screens`) | — |

Publication et envoi : en deux temps, comme dans la vidéo. Nadia prépare et montre le
brouillon, puis l'envoi ne part que sur un ordre explicite et distinct (« publie »,
« envoie »), jamais dans la même phrase que la demande de rédaction. C'est la barrière
déjà utilisée par Nadia (`detect_send_confirm`), étendue à la voix.

## 16. Points ouverts

- Fournisseur d'image : **Lot 6**, `google/gemini-2.5-flash-image` (`LIVE_IMAGE_MODEL`).
- Actions sur le PC : DEC-039 + **DEC-044** (écran, clic/frappe au centre d'une fenêtre allowlist, Valider obligatoire). Pas de capture d'écran LLM.
- Dossier / fichier : **find** Bureau + Documents + Téléchargements (`live_pc_find`). Pas tout le disque.
- Recherche Live : **budget 10 s** (`live_web_search`) — Google News / Wikipedia / DDG, Tavily optionnel. Pas de pipeline R&D sur `/live`.
- [À COMPLÉTER : captures d'écran de la vidéo (1:52, 2:15, 3:00, 21:00) fournies par
  Emilie, pour reproduire la mise en page réelle du cockpit.]