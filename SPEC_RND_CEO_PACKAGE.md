# SPEC — Package CEO R&D (post-comité)

> Phase 6 implémentée. Référence pour `.cursor/rules/rnd_dossier.mdc`.

## Fixes UX prioritaires (post-phase 3)

| Problème | Fix |
|---|---|
| Footer pitch (« 0/10 sections · Fermer ») chevauche le chat comité | Masquer le footer quand `viewMode === "committee"` dans `rnd-pitch-modal.tsx` |
| Bouton COO flottant se superpose au chat comité sur `/rd` | Ne pas monter `CooDrawer` (ni `QuickCaptureButton`) sur la route `/rd` |

## Fin de réunion — comité + brainstorm

Objectif : transformer la clôture de session en **handoff structuré** vers le dossier CEO.

- Bouton explicite + intent NL (« fais-moi le dossier », « génère le CR »)
- CR structuré (décisions, sections validées, actions, risques ouverts)
- S'inspirer du compte-rendu brainstorm (`agents/brainstorm_agent.py`)
- Aujourd'hui : `close_session` produit une synthèse légère PM + placeholders — à enrichir

## Dossier CEO (phase 6)

Templates par typologie de branche (`branch` sur `rnd_dossiers`) :

### App / SaaS
- Executive summary (1 page)
- Business model & pricing (grille `pricing_model`)
- Risques produit / marché
- R&D transverse IA (coûts agents, stack)

### Robotique / Hardware full stack
- 3 piliers : hardware / app / IA
- Réglementation (RGPD, CE, certifications)
- Industrialisation & BOM (`manufacturing`)
- COGS / OPEX détaillés
- Matrice risques technique + supply chain

### Jeu / 3D
- Perfs cibles (FPS, plateformes)
- Réseau / multijoueur si applicable
- Direction artistique (`lore`, `visual_identity`)

### Master summary (portfolio)
- Roadmap portfolio ALNUA
- **Matrice dispatch** : qui fait quoi, quels livrables envoyer à quel pôle
- COO intervient **après** validation CEO — pas dans la salle de réunion R&D

## Pipeline cible

```
Idée → Dossier sections → Comité NL → CR structuré → Deck PDF (phase 4)
  → Package CEO (phase 6) → Validation CEO → Dispatch COO (phase 6)
  → Conception / dev (pôles) → Fiche produit (phase 7)
```

## Fichiers impactés (phase 6)

- `agents/rnd_ceo_agent.py` (nouveau)
- `services/rnd_ceo_package.py` (templates par branch)
- `agents/rnd_committee_agent.py` — enrichir `close_session`
- `web/src/components/rnd/rnd-ceo-panel.tsx`
- Tables : champs `ceo_status`, `ceo_note` déjà présents sur `rnd_dossiers`
