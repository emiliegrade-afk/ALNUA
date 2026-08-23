# ALNUA Hub — Mode d'emploi : Arbres d'hypothèses R&D

> Guide pour Emilie — exploration R&D (Arbor-lite)  
> Dernière mise à jour : juin 2026

---

## C'est quoi, en une phrase ?

Quand tu dis *« lance une recherche R&D robotique »*, au lieu d'un seul rapport qui disparaît dans le vide, le Hub :

1. **Pose une question large** (la racine de l'arbre)
2. **Teste plusieurs directions** en parallèle (les branches)
3. **Garde tout** — même ce qui échoue — pour ne pas refaire les mêmes erreurs
4. Te propose de **passer au dossier** seulement ce qui vaut le coup

C'est inspiré d'**Arbor** (recherche scientifique Google/DeepMind) : un coordinateur qui accumule, des exécuteurs qui testent une idée chacun.

```
        [robotique — racine]
           /    |    \
      B2B    hardware   SaaS
       ✂️      ★ merged   🔍 explored
```

- **★ merged** = bon candidat → tu peux faire un **dossier**
- **✂️ pruned** = écarté, mais l'insight reste dans l'arbre
- **🔍 explored** = intéressant mais pas encore un produit

---

## À quoi ça sert vs ce que tu avais déjà ?

| Outil Hub | Rôle |
|-----------|------|
| **Bibliothèque** | Archive des recherches web (fiches par bureau) |
| **Centre R&D → Propositions** | Idées scorées GO / MAYBE / NO (cycle auto hebdo) |
| **Dossiers R&D** | Vrai projet structuré (marché, MVP, finance, comité…) |
| **Arbres** *(nouveau)* | **Explorer un sujet** en testant plusieurs hypothèses, avec mémoire |

**Arbre** = phase d'**exploration**.  
**Dossier** = phase de **construction** du projet.

---

## Quand l'utiliser ?

### Oui — utilise un arbre quand :

- Tu as un sujet large : *robotique*, *IA locale*, *DiffusionGemma*, *agents MCP*…
- Tu ne sais pas encore quelle direction prendre (B2B ? hardware ? intégration Hub ?)
- Tu veux qu'Alex (R&D) **creuse plusieurs pistes** sans tout oublier

### Non — passe direct au dossier quand :

- Tu as déjà une idée précise : *« app de gestion van offline »*
- Tu veux juste archiver une veille → **Bibliothèque**
- Tu veux le pipeline auto d'idées → **Lancer un cycle R&D**

---

## Mode d'emploi — Hub web

### 1. Ouvrir

- URL : `http://localhost:3000/rd`
- Onglet : **Arbres**

### 2. Lancer une investigation

- Tape un sujet (ex. `robotique`, `DiffusionGemma pour Nadia`)
- Ou clique la carte **DiffusionGemma** dans « Veille R&D »
- Bouton **Lancer**

**Ce qui se passe (3–8 min, en arrière-plan) :**

- Racine : cartographie du sujet
- 3 branches auto : ex. B2B, intégration Hub, grand public
- Chaque branche = recherche web + brief + score /30
- Tu peux fermer la page ; l'arbre se remplit tout seul

### 3. Lire le graphe

| Couleur | Statut | Signification |
|---------|--------|----------------|
| Vert | **merged** | Fort potentiel — candidat dossier |
| Ambre | **explored** | Testé, à creuser ou laisser |
| Bleu | **running** | En cours |
| Gris | **pending** | Pas encore lancé |
| Rouge | **pruned** | Écarté (mais l'insight reste) |

**Clique un nœud** → panneau à droite avec titre, hypothèse, score, insight.

### 4. Agir sur une branche

| Bouton | Effet |
|--------|--------|
| **Investiguer** | Relance une recherche sur cette branche seule |
| **+3 branches IA** | Alex propose 3 sous-pistes à partir de celle-ci |
| **Ajouter branche** | Ta propre hypothèse (titre + texte) |
| **Dossier** | Crée une proposition R&D + dossier (enrichissement ~30–60 s) |
| **Merger** / **Pruner** | Toi tu décides (override manuel) |

Après **Dossier** → lien **Ouvrir le dossier** → onglet Dossiers.

### 5. Benchmark latence (DiffusionGemma)

Bouton **Benchmark latence** sous la veille :

- Mesure la vitesse **OpenRouter** (ce que tu utilises aujourd'hui)
- Compare aux chiffres **DiffusionGemma** (modèle local Google, pas encore installé chez toi)
- **À quoi ça sert :** savoir si, quand tu auras le 2e SSD, un modèle local vaut le coup pour les ack Telegram ultra-rapides

Ce n'est **pas** un test de DiffusionGemma sur ton PC — c'est une comparaison indicative.

---

## Mode d'emploi — Telegram (Nadia)

Message type :

```
lance une recherche R&D robotique
```

**Réponse immédiate :**

> 🌳 Arbre R&D lancé — racine + 3 branches…

**Puis (plusieurs messages, ~3–8 min) :**

- Un bilan par branche (score, insight, résumé)
- Un message final : combien explorées / mergées / élaguées

**Pour voir le détail visuel** → Hub → R&D → Arbres.

Autres formulations qui marchent :

- `recherche R&D DiffusionGemma`
- `investigue la robotique logistique`

---

## Exemple concret — « robotique »

1. **Telegram** : `lance une recherche R&D robotique`
2. **Attendre** les messages (faire autre chose)
3. **Hub → Arbres** : ouvrir l'arbre `robotique`
4. **Lire le graphe** : une branche verte ★ ?
5. **Cliquer** cette branche → **Dossier**
6. **Onglet Dossiers** : enrichissement auto (sections, business case…)
7. **Comité / CEO** : workflow dossier habituel

Si tout est rouge ✂️ → le sujet est peut-être trop large ou pas aligné ALNUA ; relance avec un angle plus précis : *« cobots éducation open-hardware »*.

---

## DiffusionGemma — c'est quoi pour toi ?

Modèle Google (juin 2026) qui génère du texte **par blocs parallèles** (~4× plus rapide que l'habituel sur GPU).

- **Pas encore pour toi** (pas de 2e SSD / pas installé).
- **Dans l'arbre**, quand le sujet touche l'IA, Alex peut proposer des branches du type :
  - *Nadia PC : ack Telegram local*
  - *Infilling dans le pipeline coding*

Le benchmark te dit : *« OpenRouter met ~X ms ; DiffusionGemma pourrait être ~Y× plus rapide en local »* — pour décider plus tard.

---

## Schéma mental (ton flux CEO)

```
Idée vague ou sujet large
        ↓
   🌳 ARBRE (exploration)
        ↓
   Branche ★ merged
        ↓
   📁 DOSSIER (projet structuré)
        ↓
   Validation CEO → dispatch équipes
```

---

## Démarrer / relancer le Hub

Si Telegram dit « Hub lent ou arrêté » :

1. Double-clic sur **Demarrer-Hub.bat** (dossier `C:\Dev\ALUNA_HUB`)
2. Attendre ~1 min
3. Hub web : `http://localhost:3000`
4. API : port lu dans `data\hub_active_port.txt` (souvent 8003)

---

## Ce que tu n'as pas à faire

- Pas besoin de comprendre Arbor, les APIs ou le JSON
- Pas besoin de tout merger — seulement ce qui t'intéresse
- Pas besoin d'installer DiffusionGemma maintenant
- Les branches **pruned** ne sont pas des erreurs : elles évitent de retester la même piste

---

## En résumé

**L'arbre R&D = ton laboratoire d'idées avec mémoire.**

Tu poses un sujet → le Hub teste plusieurs directions → tu promotes en dossier ce qui mérite d'être un vrai projet ALNUA.

---

*Fichier généré depuis ALNUA Hub — `services/rnd_hypothesis_tree.py`*
