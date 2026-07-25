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
| DEC-006 | `X-Hub-Key` obligatoire hors développement | 2026-06-12 | Active |
| DEC-007 | Sanitizing désactivé sur `agents_pole.py` (PII) | — | Active |
| DEC-008 | OpenHands (pipeline autonome) + Aider (fix ciblés) en parallèle | 2026-06-11 | Active |
| DEC-009 | Intégration Nwiro/UE5 vs règle "Pas d'UE5" | 2026-06-11 → ? | **À trancher** |

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
**Décision :** les routes Hub API exigent le header `X-Hub-Key` ; seule l'exécution
avec `ENVIRONMENT=development` permet de démarrer sans clé.
**Commit :** `7c86370` ("feat(security): require X-Hub-Key on Hub API routes").
**Risque résiduel documenté :** si `ENVIRONMENT` est mal positionné en prod, l'API
démarre quand même sans clé — voir vérification dans `BUGS.md`.

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

### DEC-009 — Intégration Nwiro/UE5 vs règle "Pas d'UE5" — **À trancher**
**Constat :** `CLAUDE.md` liste "Pas d'UE5 — aucune intégration Unreal Engine dans
aucun agent" comme règle invariante. Pourtant `skills/skill_nwiro.py` (client MCP pour
le plugin Unreal Engine 5 "Nwiro", 209 outils : Blueprints, Materials, PIE Runtime...)
existe et est référencé par `game_director_agent.py`, `dev_gaming_agent.py` et
`coo_agent.py`. En parallèle, une intégration Godot 4 existe aussi (skill
`.claude/skills/alnua-godot/`, `services/workflow_engine.py`,
`web/src/lib/console/departments.ts`).
**Ce qui n'est pas tranché :** est-ce que Nwiro/UE5 est un vestige à retirer (la règle
"Pas d'UE5" est la version à jour de l'intention), ou est-ce que la règle documentée
dans `CLAUDE.md` est obsolète (Nwiro/UE5 a été adopté depuis et la doc n'a pas suivi) ?
Les deux lectures sont plausibles depuis le code seul — decision produit, pas technique.
**Action :** ne pas toucher au code tant que ce n'est pas tranché par Emilie. Entrée
laissée ouverte volontairement plutôt que suppressée ou "Active" par défaut.
