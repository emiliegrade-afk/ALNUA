# Portraits d'agents

Un fichier par agent, nommé **exactement** avec l'`id` de l'agent tel que défini
dans `web/src/lib/agent-bureau.ts` (`BUREAU_AGENTS[].id`) :

```
coo.png          → Aria Voss
dev_app.png      → Théo Laurent
dev_backend.png  → Hao Chen
inès…            → voir la liste complète dans agent-bureau.ts
```

## Format attendu

- PNG, carré, **512×512 px** minimum (l'avatar est rendu jusqu'à 96 px avec du
  `object-cover`, une source plus petite pixelise sur les écrans HiDPI).
- Cadrage portrait, visage centré dans le tiers supérieur — le composant
  applique un masque circulaire.
- Fond sombre de préférence (obsidienne) : les portraits sont posés sur
  `#080808` et un fond clair crée un halo visible sur le bord du cercle.

## Comportement sans fichier

`web/src/components/shared/agent-avatar.tsx` charge
`/agents/portraits/{id}.png` via le manifeste généré
(`web/scripts/sync-portraits.mjs`, lancé en `predev`/`prebuild`) et bascule
sur un **monogramme** si l'id n'est pas dans le manifeste.

Pour remplacer des stubs monogrammes par des portraits IA (OpenRouter Images) :
`python scripts/fill_missing_agent_portraits.py` (nécessite crédits OpenRouter).
Déposer un PNG puis `npm run sync:portraits` (ou redémarrer `next dev`) suffit.
