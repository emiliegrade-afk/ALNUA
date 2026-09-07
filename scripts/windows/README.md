# Scripts Windows avancés

Ces `.bat` ne sont **pas** destinés au quotidien. À la racine du projet, utilise seulement :

| Fichier | Usage |
|---------|--------|
| `Installer ALNUA Hub.bat` | Une fois |
| `ALNUA Hub.bat` | Démarrer |
| `Arreter ALNUA Hub.bat` | Arrêter |
| `ALNUA Desk.bat` | Chat PC (Spark · Nadia) |
| `Nadia Desktop.bat` | Alias → ALNUA Desk |

## Contenu de ce dossier

| Fichier | Rôle |
|---------|------|
| `Demarrer-Hub.bat` | Démarrage avec fenêtre CMD visible (debug) |
| `Ouvrir-Hub.bat` / `Ouvrir ALNUA Hub.bat` | Ouvre le navigateur / relance si besoin |
| `Arreter-Hub.bat` | Alias de l’arrêt (préférer la racine) |
| `Relancer Hub.bat` | Redémarrage complet |
| `Relancer agents.bat` | Wake Academy / pipeline |
| `Reparer Hub Web.bat` | Cache Next.js |
| `Installer raccourcis ALNUA.bat` | Recrée les raccourcis Bureau (via `setup-hub-shortcuts.ps1`) |
| `Demarrer_Nadia.bat` | Ancien lanceur (préférer `ALNUA Desk.bat` à la racine) |
| `run_telegram_bot.bat` | Bot Telegram seul |

Les vrais scripts PowerShell restent dans `scripts/*.ps1`.
