# ALNUA Hub — Bible / Classeur

Point d’entrée documentation **après** `AGENTS.md` et `CLAUDE.md` (racine).
Ce dossier regroupe specs, guides, statut d’implémentation et archives —
pour que la racine du repo reste lisible.

## Lire dans cet ordre

| Priorité | Où | Pour quoi |
|----------|-----|-----------|
| 1 | [`../AGENTS.md`](../AGENTS.md) | Ordre de lecture universel |
| 2 | [`../CLAUDE.md`](../CLAUDE.md) | Briefing code (stack, agents, invariants) |
| 3 | [`../README.md`](../README.md) | Install / run |
| 4 | [`../ALNUA_OVERVIEW.md`](../ALNUA_OVERVIEW.md) | Produit / organisation |
| 5 | Gouvernance vivante (racine) | `ROADMAP` · `DECISIONS` · `BUGS` · `CHANGELOG` |
| 6 | Ce classeur | Specs, architecture détaillée, guides, archives |

## Classeur

| Dossier / fichier | Contenu |
|-------------------|---------|
| [`classeur/`](classeur/) | Architecture, testing, implementation status, audits, todos |
| [`specs/`](specs/) | Contrats feature (`SPEC_*`) — Brand, R&D, UE5.8, workflows |
| [`guides/`](guides/) | MCP Cursor, [sécurité VPS](guides/SECURITY_HARDENING.md), autonomie, n8n |
| [`getting-started/`](getting-started/) | [Install / lancer le Hub](getting-started/installation.md) |
| [`api/`](api/) | [Auth Hub-Key](api/authentication.md) |
| [`archive/`](archive/) | Plans terminés, assainissement historique, vieux changelog |

## Racine volontairement courte

Restent à la racine uniquement : `AGENTS` · `CLAUDE` · `README` · `ALNUA_OVERVIEW` ·
`ROADMAP` · `DECISIONS` · `BUGS` · `CHANGELOG`.

Tout le reste documentaire utile vit ici. Ne pas re-créer des `SPEC_*.md` à la racine.
