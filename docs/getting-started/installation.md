# Installation — ALNUA Hub

## C'est quoi ?

ALNUA Hub est le cockpit de ton entreprise virtuelle : une interface web où tu pilotes des agents IA (COO, PM, dev, marketing, R&D…). Tout tourne en local sur ton PC — pas besoin de serveur cloud pour commencer.

## Prérequis

| Outil | Version | Pourquoi |
|-------|---------|----------|
| **Python** | 3.11+ | API backend + agents |
| **Node.js** | 18+ | Interface web (Next.js) |
| **Git** | récent | Cloner le dépôt |
| **Comptes** | Supabase + OpenRouter | Base de données et modèles IA |

Tu auras aussi besoin d'un fichier `.env` avec tes clés (voir ci-dessous). **`HUB_API_KEY` est obligatoire** — l'API refuse les requêtes non authentifiées.

## Première installation (5 minutes)

### 1. Cloner le projet

```powershell
cd C:\Dev
git clone <url-du-repo> ALUNA_HUB
cd ALUNA_HUB
```

### 2. Environnement Python

```powershell
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

### 3. Configurer `.env`

```powershell
copy .env.example .env
```

Ouvre `.env` et remplis au minimum :

- `SUPABASE_URL` et `SUPABASE_KEY`
- `OPENROUTER_API_KEY`
- `HUB_API_KEY` — choisis une clé secrète longue (ex. un mot de passe généré)

> Ne partage jamais ton `.env`. Consulte [SECURITY_HARDENING.md](../guides/SECURITY_HARDENING.md) pour les bonnes pratiques.

### 4. Lancer l'installateur Windows

Double-clic sur **`Installer ALNUA Hub.bat`** à la racine du projet.

L'installateur :

1. Vérifie que Python (`.venv`) est prêt
2. Propose `npm install` dans `web/` si besoin
3. Vérifie que `.env` existe
4. Crée le raccourci Bureau **ALNUA Hub**

Options PowerShell avancées :

```powershell
.\scripts\install-hub.ps1 -InstallNpm    # npm sans question
.\scripts\install-hub.ps1 -SkipNpm       # ignorer npm
.\scripts\install-hub.ps1 -Startup       # + démarrage à la connexion
```

## Démarrer / arrêter au quotidien

| Action | Comment |
|--------|---------|
| **Démarrer** | Double-clic **ALNUA Hub** (Bureau) |
| **Interface** | http://localhost:3000 (s'ouvre automatiquement) |
| **Arrêter** | Double-clic **`Arreter ALNUA Hub.bat`** |

### Expérience « produit » (comme une app installée)

1. **Une fois** : `Installer ALNUA Hub.bat` → raccourci Bureau.
2. **Chaque jour** : double-clic l'icône → le Hub démarre **sans fenêtre CMD** (launcher VBS + supervisor caché).
3. Le navigateur s'ouvre. Tu n'as **pas** de console noire qui reste ouverte.
4. Pour couper : `Arreter ALNUA Hub.bat`.

Sous le capot : `scripts/launch-hub-silent.vbs` → `start-all.ps1` → `hub_supervisor.py` (API **:8003** + web **:3000**, processus enfants sans fenêtre).

Ce n'est pas encore un `.exe` signé type store — c'est le même modèle qu'un outil desktop pro local (install → icône → app). Le pack VPS / distribution large vient plus tard.

## Hub H24 à la connexion Windows

Pour que le Hub démarre à chaque ouverture de session :

```powershell
.\scripts\install_hub_daemon_startup.ps1
```

Ou lors de l'installation :

```powershell
.\scripts\install-hub.ps1 -Startup
```

Désinstaller :

```powershell
.\scripts\install_hub_daemon_startup.ps1 -Remove
```

## Vérifier que tout va bien

```powershell
.\scripts\hub-status.ps1
```

Affiche l'état de l'API, du web, du supervisor et des bots Telegram. **Code de sortie 0** = API saine.

Test manuel rapide :

```powershell
Invoke-RestMethod http://127.0.0.1:8003/health
```

## Dépannage rapide

| Symptôme | Piste |
|----------|-------|
| `venv introuvable` | Relance les commandes Python de l'étape 2 |
| Web ne charge pas | `cd web; npm install` puis relance `ALNUA Hub.bat` |
| API 401 / clé refusée | Vérifie `HUB_API_KEY` dans `.env` |
| Logs | `data\hub_supervisor.log` |

## Plus tard : déploiement VPS

Un `docker-compose.yml` existe à la racine pour un futur pack serveur. Ce guide couvre uniquement l'installation locale Windows — le déploiement VPS sera documenté séparément.

## Suite

- [Premiers 15 minutes](./first-15-minutes.md) — première conversation avec les agents
- [Concepts](./concepts.md) — rooms, workflows, mémoire
- [Sécurisation](../SECURITY_HARDENING.md) — durcissement API et secrets
- [Manuel utilisateur](../guides/user-manual.md) — *(à venir)*
