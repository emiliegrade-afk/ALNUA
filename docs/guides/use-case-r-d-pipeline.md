# Use case — Pipeline R&D

## Objectif
Cycle hebdomadaire autonome : veille → idées → comité → package CEO → dispatch.

## Flow
1. **Vendredi 18h** — cron `run_rnd_cycle` (scheduler)
2. **rnd_center** mine anti-patterns + génère idées
3. **Comité multi-agents** débat en langage naturel
4. **Package CEO** avec actions dispatchables
5. **9 statuts** : raw → published

## Déclenchement manuel
```
Aria, lance un cycle R&D sur les tendances IA agents
```

## UI
- `/rd` — hub R&D
- `/ceo` — cockpit décisions

## API
```bash
curl -X POST http://localhost:8003/v1/rnd/cycle/run -H "X-Hub-Key: $KEY"
```
