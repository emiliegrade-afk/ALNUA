---
ref: GDD-WYR-{SLUG}-001
type: biome
statut: concept
date_création: YYYY-MM-DD
agents_assignés: game_director, dev_gaming, level_designer
lore_refs: LORE-WYR-XXX
asset_refs: ASSET-WYR-XXX
---

# GDD-WYR-{SLUG} — {Titre : Biome / Créature / Système}

## 01 — VISION CRÉATIVE

### Phrase de concept (1 ligne)
{Ce que le joueur ressent en 10 secondes}

### Piliers de design (3 max)
1. {Pilier 1}
2. {Pilier 2}
3. {Pilier 3}

### Inspirations
- Jeu : {Titre} — {emprunt}
- Mythologie / Littérature : {référence}
- Artistique : {référence visuelle}

---

## 02 — LORE

### Contexte historique
{Origine, époque, raison d'être}

### Place dans la cosmologie Wyrdheim
{Lien Seigneurs Wyrd, factions, événements}

### Secrets
- Visible :
- Caché (quêtes secondaires) :
- Profond (lore maître) :

### Personnages liés
| Ref | Nom | Rôle | Faction | Statut |
|-----|-----|------|---------|--------|
| LORE-WYR-XXX | | | | |

---

## 03 — DIRECTION ARTISTIQUE

### Palette
- Dominante : {hex} — {ambiance}
- Accent : {hex}
- Lumière / Ombres :

### Style visuel
{3-5 phrases — surfaces, végétation, brume, courbes…}

### Ambiance lumière
| Moment | Description | Couleur |
|--------|-------------|---------|
| Aube | | |
| Nuit | | |

### Audio
- Ambiance :
- Thème musical :
- SFX caractéristiques :

---

## 04 — ASSETS REQUIS

### Environnement
| Ref | Asset | Polycount | Source | Statut |
|-----|-------|-----------|--------|--------|
| ASSET-WYR-ENV-001 | | | Epic lib / ComfyUI | pending |

### Créatures
| Ref | Asset | Animations | Source | Statut |
|-----|-------|------------|--------|--------|

### VFX / Materials / Audio
{Tableaux ASSET-WYR-VFX, MAT, SFX}

---

## 05 — MÉCANIQUES GAMEPLAY

### Interaction joueur
{Comment le joueur interagit}

### Règles
- Règle 1 : {valeurs numériques}
- Règle 2 :

### Équilibrage
| Paramètre | Valeur | Justification |
|-----------|--------|--------------|
| HP | | |
| Dégâts | | |
| XP | | |

### Events / triggers
- Entrée zone :
- Conditions : météo, heure, faction, niveau

---

## 06 — SPÉCIFICATION UE5

### Blueprint / C++
- Logique : Blueprint / C++ — {justification}
- Composants : PCG, Niagara, Sequencer…
- **Assets Epic library** : {liste Marketplace/Fab déjà possédés}

### PCG
- Densité spawn :
- Performance budget : {ms max}

### Performance
- 60fps PC / 30fps console
- LOD : {distances}

### Nwiro
```
Prompt biome_generation :
"{prompt exact}"

Tools prioritaires :
- biome_generation
- pcg_execute
- actor_spawn
```

---

## 07 — PIPELINE

1. [ ] Lore validé → LORE-WYR-XXX
2. [ ] Concept art DA (Emilie)
3. [ ] Assets ComfyUI → TripoSR → UE5
4. [ ] Biome Nwiro → review PIE
5. [ ] VFX + audio
6. [ ] Balancing → statut `validé`

---

## 08 — JOURNAL
| Date | Auteur | Entrée |
|------|--------|--------|
| | Emilie | Création |
