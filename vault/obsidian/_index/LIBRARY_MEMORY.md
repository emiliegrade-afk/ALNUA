# Bibliothèque & mémoire agents

Le vault Obsidian central (`OBSIDIAN_VAULT_PATH`, défaut `D:\ObsidianVault`) est la **mémoire durable** d'ALNUA.

## Layout

| Dossier | Rôle |
|---------|------|
| `library/{bureau}/` | Fiches exportées depuis `data/bureau_library.json` (summary + digest complets) |
| `library/_index/TOPICS.md` | Catalogue de sujets scannable par les agents |
| `library/_digests/` | Synthèses de sujets (learn on demand) |
| `memory/agents/{agent_id}/` | Leçons distillées par agent |
| `wyrdheim/`, `apps/`, `rnd/`, `collabs/`, `daily/` | Projets / lore / specs |

## Workflow

1. Bootstrap dossiers : `python scripts/bootstrap_obsidian_vault.py` (appelle `ensure_vault_layout`)
2. Export initial (~5k fiches) : `python scripts/export_library_to_vault.py`
3. Optionnel Chroma : `python scripts/export_library_to_vault.py --index-chroma`
4. API : `GET /library/topics`, `POST /library/topics/{slug}/learn`, `POST /library/vault/sync`

## Apprentissage hybride

- **Catalogue** = ce que les agents savent pouvoir apprendre
- **Digest / notes vault** = contenu riche (pas tronqué à 220 chars)
- **Mem0** = leçons distillées + compression auto
- **Knowledge skills** = `skills/knowledge/{slug}/SKILL.md` si sujet récurrent / hot

Ne synchronise pas ce vault avec OneDrive.
