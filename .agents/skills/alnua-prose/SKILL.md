# /alnua-prose — Prose anti-AI pour ALNUA
> Adapté de stop-slop (hardikpandya) pour Sofia (Content) et Camille (Marketing).
> Invoque avec `/alnua-prose` avant de générer ou réviser du contenu éditorial.

## Objectif
Produire du contenu qui sonne humain, pas généré. Aucun "AI tell" dans le texte final livré par Sofia ou Camille.

---

## Règles obligatoires — NE JAMAIS violer

### 1. Interdictions absolues de vocabulaire
Bannir ces mots/formules de tout output :
- **Adverbes vides** : `très`, `vraiment`, `absolument`, `fondamentalement`, `essentiellement`, `clairement`, `évidemment`, `incroyablement`, `remarquablement`
- **Ouvertures génériques** : `Dans le paysage [X] actuel`, `À l'ère du numérique`, `Il est important de noter`, `Il est crucial de`, `En conclusion`, `Dans cet article`, `Plonger dans`
- **Remplissage rhétorique** : `explorer les nuances`, `naviguer dans la complexité`, `déverrouiller le potentiel de`, `à la pointe`, `révolutionnaire`, `game-changer`, `synergies`, `holistique`
- **Auto-référence** : `Cet article va...`, `Nous allons explorer...`, `Laissez-moi vous expliquer...`
- **Intensificateurs creux** : `robuste`, `complet`, `global`, `transformateur`, `percutant`, `puissant` (sauf si justifié par des chiffres)

### 2. Règles de structure
- **Listes à puces** : max 4 items. Si tu as 8 points, c'est 2 paragraphes, pas 8 puces.
- **Paragraphes courts** : 2-4 phrases max. Jamais de blocs > 6 lignes.
- **Pas de sous-titre toutes les 2 lignes** : les H2/H3 servent à organiser, pas à compenser le vide.
- **Pas de "premier/deuxièmement/troisièmement"** : le texte doit fluir naturellement.

### 3. Règles de ton
- Concrétiser chaque claim avec un exemple, un chiffre, ou un cas précis.
- Éviter les métaphores mixtes. Une seule métaphore filée si nécessaire.
- Le contenu doit avoir un point de vue. Les agents ALNUA ont des opinions — Sofia et Camille aussi.
- Longueur : dire la chose en la moitié des mots. Si c'est trop court, c'est parfait.

---

## Checklist avant livraison (Sofia / Camille l'appliquent sur tout output)

```
[ ] Aucun mot de la liste interdite présent
[ ] Chaque claim a un exemple ou un chiffre
[ ] Pas de paragraphe > 6 lignes
[ ] Pas de liste > 4 items sans justification
[ ] L'ouverture ne commence pas par "Dans le paysage..."
[ ] La conclusion ne commence pas par "En conclusion..."
[ ] Le texte a un point de vue clair, pas juste une liste de faits
[ ] Lu à voix haute : ça sonne humain ?
```

---

## Application par agent

**Sofia (Content)** — blog posts, newsletters, Discord announcements :
- Écrire comme si c'était un tweet étendu, pas un livre blanc.
- Chaque phrase doit gagner sa place. Si elle n'ajoute rien, elle sort.

**Camille (Marketing)** — copy, landing pages, product hunt descriptions :
- Max 1 superlatif par texte. "Le meilleur" est interdit sauf preuve.
- Le CTA est une phrase simple et active : "Essaie 30 jours gratuit" pas "Découvrez dès aujourd'hui notre solution innovante".

---

## Exemple : avant/après

**❌ Version AI :**
> Dans le paysage technologique actuel, il est crucial de comprendre comment ALNUA Hub révolutionne fondamentalement la façon dont les équipes naviguent dans la complexité de la gestion de projets avec ses solutions robustes et complètes.

**✅ Version humaine :**
> ALNUA Hub coordonne 20 agents IA en parallèle. Tu poses une question à Aria (COO), elle délègue à Axel (data), Léon (spec) et Sofia (content) simultanément, et tu as le résultat en secondes.

---

## Règles de format pour Cursor
- Quand tu génères du contenu pour Sofia ou Camille, passe toujours par cette checklist.
- Si un mot interdit apparaît dans ta réponse, révise avant de livrer.
- Le standard : si un lecteur ne peut pas distinguer le texte d'un email écrit par un humain, c'est réussi.
