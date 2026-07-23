# Nomenclature ALNUA

Système de références pour retrouver bugs, lore, GDD et assets en une recherche.

## Format général

```
{TYPE}-{SCOPE}-{slug}-{numéro}
```

- **TYPE** : nature du document (APP, GDD, LORE, ASSET, BUG, COLLAB, RND)
- **SCOPE** : optionnel — `WYR` (Wyrdheim), `NWA` (Naïa World), slug app
- **numéro** : 3 chiffres incrémentaux (`001`, `002`, …)

## Types

### APP — Applications

```
APP-{slug}-001
APP-{slug}-F001   → feature P0/P1
ASSET-APP-{slug}-001
```

Exemple : `APP-naia-001`, `APP-naia-F003`

### GDD — Game Design (Wyrdheim)

```
GDD-WYR-{slug}-001
```

Types de contenu : `biome`, `créature`, `faction`, `système_gameplay`, `quête`, `event_monde`

### LORE

```
LORE-WYR-001    → Wyrdheim
LORE-NWA-001    → Naïa World
```

Catégories Supabase : `factions`, `personnages`, `lieux`, `histoire`, `magie`, `economie`, `quetes`

### ASSET (gaming)

```
ASSET-WYR-ENV-001    → environnement
ASSET-WYR-CHAR-001   → personnage / créature
ASSET-WYR-VFX-001    → effet Niagara
ASSET-WYR-MAT-001    → material
ASSET-WYR-SFX-001    → audio
```

### BUG

```
BUG-YYYYMMDD-001
```

Date = jour de découverte. Un bug = une note dans `daily/` ou issue GitHub liée.

### COLLAB — Partenariats

```
COLLAB-{slug}-001
```

### RND — Recherche Hub

```
RND-{slug}-001
```

## Frontmatter Obsidian (recommandé)

En tête de chaque note :

```yaml
ref: LORE-WYR-001
statut: draft
project: wyrdheim
category: lieux
tags: [biome, forêt]
```

Le script `obsidian_sync.py` lit ces champs pour pousser vers Supabase.

## Recherche

- Obsidian : `Ctrl+O` ou recherche full-text
- Hub : `search_lore(query)` / API GDD chunks
- Cursor : agents gaming avec refs croisées dans les templates
