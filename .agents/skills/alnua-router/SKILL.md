# ALNUA Router — Routage LLM Dynamique

Routeur LLM adaptatif dans `services/llm_router.py`. Inspiré de NadirClaw (40-70% économies). Géré par Rémi Chassagne (Contrôleur).

---

## Principe

| Mode | Trigger | Économie |
|------|---------|----------|
| Static (avant) | Tier fixe par agent dans agent_models.py | 0% |
| Dynamic (maintenant) | Score complexité 0-10 → tier adapté | estimé 20-40% |

**Règle de sécurité :** on peut monter d'un tier (upgrade si complexité élevée) mais jamais descendre sous le tier statique configuré.

---

## Usage dans un agent

```python
# Dans une méthode agent, remplacer :
raw = self.llm.complete(self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME)

# Par (si routage dynamique souhaité) :
from services.llm_router import route_to_model
model = route_to_model(self.AGENT_NAME, prompt, method_name="my_method")
raw = self.llm.complete(self.SYSTEM_PROMPT, prompt, model=model)
```

**Note :** pour la plupart des agents, le tier statique suffit. N'utiliser le routage dynamique que pour les agents ayant des méthodes à forte variabilité de complexité (COO, RnD, Analyst Business).

---

## Score de complexité (0-10)

```python
from services.llm_router import complexity_score

score = complexity_score(prompt="...", method_name="market_analysis")
# 0-3 : simple → fast
# 4-6 : moyen → standard
# 7-10 : complexe → premium
```

**Ce qui fait monter le score :**
- Longueur > 2000 chars (+3)
- Mots-clés : "compare", "stratégi", "risque", "architecture complète" (+2 par signal)
- Méthode dans `_ALWAYS_UPGRADE_METHODS` : market_analysis, strategic_brief, write_gdd, research (+3)
- JSON complexes (> 3 accolades) (+1)

**Ce qui fait descendre :**
- Longueur < 200 chars (-1)
- Méthode dans `_ALLOW_DOWNGRADE_METHODS` : sql_query, anomaly_report, triage_emails (-1)

---

## Rapport de routage (audit Rémi)

```python
from services.llm_router import routing_report

report = routing_report("coo", prompt, "strategic_brief")
# {
#   "agent_id": "coo",
#   "method": "strategic_brief",
#   "static_tier": "premium",
#   "complexity_score": 8,
#   "dynamic_tier_suggestion": "premium",
#   "final_tier": "premium",
#   "routed_model": "google/gemini-2.5-pro",
#   "upgrade_triggered": False,
# }
```

---

## Endpoints API (debug et audit)

```bash
# Quel modèle serait choisi ?
POST /services/llm-router/route
{"agent_id": "dev_app", "prompt": "...", "method_name": "review_code"}

# Rapport complet
POST /services/llm-router/report
{"agent_id": "analyst_business", "prompt": "...", "method_name": "market_analysis"}

# Score de complexité seul
POST /services/llm-router/complexity
{"agent_id": "qa", "prompt": "..."}
```

---

## Méthodes toujours upgradées (premium forcé)

```
market_analysis, strategic_brief, game_concept, write_gdd,
research, prototype_spec, debate_spec, monthly_report
```

## Méthodes pouvant être dégradées (si prompt simple)

```
sql_query, anomaly_report, triage_emails, llm_cost_alert,
bom_lookup, hardware_spec, firmware_task
```

---

## Tiers et modèles (config/agent_models.py)

| Tier | Modèle OpenRouter | Usage |
|------|-----------------|-------|
| fast | z-ai/glm-5.3-flash | Tâches structurées simples / volume |
| standard | openai/gpt-5.6-terra | Fallback si pas de modèle métier |
| premium | anthropic/Codex-sonnet-5 | COO, R&D, analyses complexes (floor routeur) |

AUTO métier : `config/agent_models_roles.py::AGENT_ROLE_MODELS` (code / raisonnement / rédaction / ops), pas un seul modèle par tier.
