---
ref: APP-{SLUG}-001
statut: draft
date_création: YYYY-MM-DD
owner: Emilie (CEO)
agents_assignés: dev_app, dev_backend, spec, qa, pm
repo_github: https://github.com/emiliegrade-afk/{slug}
---

# APP-{SLUG} — {Nom de l'application}

## 01 — VISION

### Phrase de positionnement (1 ligne)
{Ce que fait l'app, pour qui, pourquoi maintenant}

### Problème résolu
{Pain point concret, exemple utilisateur réel}

### Proposition de valeur unique
{Différenciation vs alternatives}

### Objectifs mesurables (3 mois)
- KPI 1 : {ex. 500 users actifs / semaine}
- KPI 2 : {ex. rétention J7 > 40%}
- KPI 3 : {ex. note stores > 4.2}

---

## 02 — UTILISATEURS CIBLES

### Persona primaire
- Âge / profil :
- Problème quotidien :
- Comportement :
- Déclencheur d'adoption :

### Persona secondaire
{Même structure si applicable}

---

## 03 — FONCTIONNALITÉS

### P0 — Must have (MVP)
| Ref | Feature | Description | Critère de validation |
|-----|---------|-------------|----------------------|
| APP-{SLUG}-F001 | {Nom} | {Description} | {Test d'acceptance} |

### P1 — Important (v1.1)
{Même tableau}

### P2 — Nice to have
{Même tableau}

### Hors scope
- {Ce qui NE sera PAS fait}

---

## 04 — TECH STACK

### Plateforme
- [ ] Mobile iOS + Android
- [ ] Web responsive
- [ ] PWA / Desktop

### Framework
- [ ] React Native + Expo
- [ ] Next.js 15
- [ ] Autre :

### Backend
- Supabase (PostgreSQL, Auth, Storage)
- Edge Functions : {liste}
- APIs tierces : {liste}

### Auth
- [ ] Supabase Auth
- [ ] Anonyme puis conversion
- [ ] Pas d'auth (v1)

### Déploiement
- Frontend : Vercel / Expo EAS
- CI/CD : GitHub Actions

---

## 05 — UI/UX

### Design System
- Base : {shadcn/ui, NativeWind, …}
- Tokens : {chemin}
- Composants partagés : {Naïa / Hub / nouveau}

### Couleurs
| Rôle | Hex | Usage |
|------|-----|-------|
| Primaire | | |
| Secondaire | | |
| Fond | | |

### Principes UX
1. {Principe 1}
2. {Principe 2}
3. {Principe 3}

### Flow principal
```
Onboarding → Home → Feature → Profil → Paramètres
```

### Accessibilité
- WCAG AA, touch targets 44px min

---

## 06 — DIRECTION ARTISTIQUE

### Style général
{2-3 phrases d'atmosphère}

### Références
- {App/œuvre 1} — {pourquoi}
- {App/œuvre 2}

### Assets à produire
| Ref | Asset | Format | Généré par |
|-----|-------|--------|-----------|
| ASSET-APP-{SLUG}-001 | App icon | PNG 1024 | ComfyUI |

---

## 07 — CONTRAINTES

### Timeline
- MVP : {date}
- v1.0 stores : {date}

### Risques
| Risque | Probabilité | Impact | Mitigation |
|--------|------------|--------|-----------|

---

## 08 — JOURNAL
| Date | Auteur | Entrée |
|------|--------|--------|
| {date} | Emilie | Création |
