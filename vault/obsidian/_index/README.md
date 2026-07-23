# ALNUA Vault

Mémoire humaine d'ALNUA — lore, GDD, specs apps, contrats CEO, R&D.

**Ne pas synchroniser avec OneDrive** (conflits de fichiers Obsidian).

## Structure

| Dossier | Contenu |
|---------|---------|
| `_templates/` | Modèles à dupliquer (APP, GDD, LORE, BUG, COLLAB) |
| `_index/` | Index et nomenclature |
| `wyrdheim/` | Wyrdheim Online — lore, GDD, biomes, créatures |
| `apps/` | Specs applications (Naïa, NUAWAY, etc.) |
| `rnd/` | Dossiers R&D Hub |
| `collabs/` | Contrats et partenariats CEO |
| `daily/` | Notes journalières |

## Références (nomenclature)

Voir [[nomenclature]] pour le détail.

| Préfixe | Exemple | Usage |
|---------|---------|-------|
| `APP-` | `APP-naia-001` | Spec application |
| `GDD-WYR-` | `GDD-WYR-biome-001` | Game design Wyrdheim |
| `LORE-WYR-` | `LORE-WYR-001` | Lore Wyrdheim |
| `LORE-NWA-` | `LORE-NWA-001` | Lore Naïa World |
| `ASSET-WYR-` | `ASSET-WYR-ENV-001` | Asset 3D / VFX / audio |
| `BUG-` | `BUG-20260624-001` | Bug tracker |
| `COLLAB-` | `COLLAB-partner-001` | Partenariat |
| `RND-` | `RND-diffusion-001` | Dossier R&D |

## Workflow Hub

1. Rédiger dans Obsidian (templates `_templates/`)
2. `python scripts/obsidian_sync.py` — sync lore/GDD → Supabase
3. Agents `game_director`, `dev_gaming`, `level_designer` lisent via `skill_lore_database` + GDD chunks

## Bootstrap

```powershell
python scripts/bootstrap_obsidian_vault.py
```

Copie index + templates vers `OBSIDIAN_VAULT_PATH` (défaut `D:\ObsidianVault`).
