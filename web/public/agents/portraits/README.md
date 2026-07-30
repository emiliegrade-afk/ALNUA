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
`/agents/portraits/{id}.png` et bascule sur un **monogramme** (initiales,
anneau cuivre, teinte déterministe par agent) si le fichier n'existe pas.
Déposer un PNG suffit à le faire apparaître — aucun code à modifier, aucun
redémarrage de build nécessaire en dev.
