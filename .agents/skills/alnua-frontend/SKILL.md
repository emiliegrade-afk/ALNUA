# /alnua-frontend — Checklist qualité frontend ALNUA
> Adapté de Front-End-Checklist (thedaviddias, ⭐73k) pour Théo Laurent (Dev App).
> Invoque avec `/alnua-frontend` avant tout merge de composant Next.js ou page.

## Stack frontend ALNUA
- **Framework** : Next.js (App Router)
- **Langage** : TypeScript
- **Styling** : Tailwind CSS
- **State** : React hooks + Server Components
- **API** : ALNUA Hub FastAPI (`localhost:8000`)
- **Agents UI** : `web/src/components/`

---

## Checklist complète — obligatoire avant PR

### 🔴 P0 — Bloquants (PR refusé si KO)

#### HTML & Sémantique
- [ ] Pas de `<div>` là où `<section>`, `<article>`, `<nav>`, `<main>`, `<header>` conviennent
- [ ] Chaque page a un seul `<h1>`
- [ ] Les images ont toutes un `alt` descriptif (pas `alt=""` sauf décoratif)
- [ ] Les formulaires ont des `<label>` liés aux inputs via `htmlFor`
- [ ] Pas de `tabIndex > 0` — l'ordre de focus est naturel

#### Performance
- [ ] Images : format WebP ou `next/image` avec `width`/`height` définis
- [ ] Pas d'import de bibliothèque entière pour une fonction (`import { debounce } from 'lodash'` ❌ → `import debounce from 'lodash/debounce'` ✅)
- [ ] Les Server Components restent côté server (pas de `'use client'` inutile)
- [ ] Les `useEffect` ont des dépendances correctes — pas de boucle infinie

#### TypeScript
- [ ] Pas de `any` (sauf commentaire justifié `// eslint-disable-next-line`)
- [ ] Toutes les props des composants ont un type défini
- [ ] Les réponses API sont typées (models dans `api/schemas.py` → types TS)

#### Sécurité
- [ ] Pas de clé API dans le code frontend (tout passe par les variables d'env Next.js)
- [ ] Les inputs utilisateur sont sanitisés avant envoi à l'API
- [ ] Pas de `dangerouslySetInnerHTML` sans justification

#### Accessibilité
- [ ] Contraste couleur ≥ 4.5:1 pour le texte normal, 3:1 pour le grand texte
- [ ] Les éléments interactifs sont accessibles au clavier (focus visible)
- [ ] Les modales/drawers ont `role="dialog"` et gèrent le focus trap

---

### 🟡 P1 — Importants (à corriger dans la PR)

#### UX & États
- [ ] Chaque action asynchrone a un état loading visible
- [ ] Les erreurs API sont catchées et affichées à l'utilisateur (pas de console.error silencieux)
- [ ] Les formulaires ont des états de validation inline (pas seulement submit)
- [ ] L'état vide est géré (liste vide → message, pas page blanche)

#### Responsive
- [ ] Testé sur mobile (375px), tablet (768px), desktop (1280px)
- [ ] Pas de scroll horizontal sur mobile
- [ ] Les grilles Tailwind utilisent des breakpoints cohérents (`sm:`, `md:`, `lg:`)

#### Composants ALNUA
- [ ] Les appels à l'API Hub passent par les helpers existants (pas de `fetch` direct)
- [ ] Les agents sont appelés via les routes définies dans `agents_pole.py`
- [ ] Les erreurs 4xx/5xx du Hub sont catchées proprement
- [ ] Les scores de compétition sont mis à jour après chaque action agent

#### Code Quality
- [ ] Pas de console.log en production (utilise les logs structurés Next.js)
- [ ] Les magic strings sont dans des constantes (`AGENT_IDS`, etc.)
- [ ] Les composants > 200 lignes sont découpés

---

### ⚪ P2 — Recommandés

#### SEO (si page publique)
- [ ] `<title>` et `<meta description>` définis via `metadata` Next.js
- [ ] URL slug lisible (`/agents/analyst-data` pas `/agents/4e8f`)
- [ ] Open Graph tags présents pour les pages partageables

#### Animation & Polish
- [ ] Les transitions utilisent Tailwind (`transition-all duration-200`) pas de `setTimeout` CSS
- [ ] Les loading states utilisent un skeleton, pas un spinner générique
- [ ] Dark mode respecté si le design system ALNUA l'implémente

---

## Agents ALNUA — points de contact frontend

| Page | Composants clés | Agents impliqués |
|------|-----------------|-----------------|
| `/app` | DevAppView, DevBackendView | dev_app, dev_backend |
| `/gaming` | GameDirectorView, DevGamingView | game_director, dev_gaming, level_designer |
| `/rd` | BrainstormView, RndView | brainstorm, rnd_agent |
| `/comms` | ContentView, MarketingView | content, marketing |
| `/accounting` | AccountingView, ControllerView | accounting, controller |
| `/analytics` | BusinessView, DataView | analyst_business, analyst_data |
| `/hardware` | HardwareView, EmbeddedView | hardware, embedded_dev |
| `/secretary` | SecretaryView | secretary |
| Dashboard | Leaderboard, Scores | competition system |

---

## Commandes utiles (Théo les applique)

```bash
# Type check
npx tsc --noEmit

# Lint
npx next lint

# Build production (doit passer sans erreur ni warning)
npm run build

# Test performance Lighthouse (cible : perf > 80, a11y > 90)
npx lighthouse http://localhost:3000 --view
```

---

## Règle d'or Théo
> Un composant est prêt quand il passe la checklist P0 + P1 **et** qu'un utilisateur peut l'utiliser sans avoir à deviner ce qu'il fait.
