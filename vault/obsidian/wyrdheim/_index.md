# Wyrdheim Online

MMO dark fantasy nordique — lore, biomes, créatures, factions, quêtes, GDD.

## Dossiers

| Chemin | Contenu |
|--------|---------|
| `lore/` | Entrées `LORE-WYR-*` — sync → Supabase `lore_entries` |
| `gdd/` | Documents `GDD-WYR-*` — sync → Supabase `gdd_chunks` |
| `biomes/` | Notes libres liées aux biomes (liens vers GDD) |
| `creatures/` | Notes libres créatures / NPC |

## Agents assignés

- **Mira Chen** (`game_director`) — vision, lore, quêtes, économie
- **Nova Fischer** (`dev_gaming`) — UE5, Nwiro, Blueprint
- **Finn Larsen** (`level_designer`) — level design, PCG

## Pipeline asset

1. Lore validé → GDD rédigé (template `_templates/GDD-WYR-template.md`)
2. Concept art ComfyUI (RunPod) → TripoSR mesh → import UE5
3. Bibliothèque Epic existante + assets custom via Nwiro MCP
4. Review PIE → statut `validé`

## Projet UE5

`D:\UE5\Projects\Wyrdheim` — Third Person, Blueprint, DDC `C:\UE5Cache`
