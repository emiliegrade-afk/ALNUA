# Premiers 15 minutes — ALNUA Hub

Session guidée pour Emilie. Prérequis : Hub installé et démarré
([installation](./installation.md) — icône Bureau **ALNUA Hub**).

Ouvre http://localhost:3000. Aucune fenêtre CMD ne doit rester ouverte.

---

## Minute 0–3 — Vérifier que tout tourne

Dans PowerShell :

```powershell
.\scripts\hub-status.ps1
Invoke-RestMethod http://127.0.0.1:8003/health
```

- Status **0** / API saine → OK.
- Navigateur : http://localhost:3000 → **Command Center**.
- Optionnel : http://localhost:3000/landing (page marketing) puis `/ceo`.

Canonique santé API : **`/health`** (pas besoin de `/v1`).

---

## Minute 3–7 — Parler aux agents

1. Sur le Command Center (`/`), ouvre le **tiroir Assistants** (bouton flottant).
2. Demande à **Aria** (COO) : *« Priorités du jour »*.
3. Passe à **Nadia** : *« Qu’est-ce qui attend mon attention ? »*.
4. Si des 👍/👎 apparaissent sur une réponse : un 👎 peut déclencher une regen + une leçon mémoire — utile, pas obligatoire.

Tu n’as **pas** besoin d’un onglet « Assistants » dans `/ceo` : le tiroir est global sur la console.

---

## Minute 7–10 — Explorer les bureaux

| Où | Quoi faire |
|----|------------|
| `/hq` | Carte HQ — clique **Secrétariat**, **R&D**, **Salle de réunion**… |
| `/ceo` | Regarde les workflows en attente / gate Academy |
| `/rd` | Ouvre l’onglet **Arbres** puis **Dossiers** (labo d’idées) |
| `/openroom` | Salon agents (roster complet, pas « 9 salles ») |
| `/academy` | Aperçu des niveaux / sprints agents |
| `/analytics` | Métriques si tu es curieuse |

Rappel **arbres** : mindmap d’hypothèses → tu gardes / tues une branche → une branche gardée devient un **dossier**. Détail : [manuel §6](../guides/user-manual.md).

---

## Minute 10–12 — Un coup d’œil API (optionnel)

```powershell
$k = "TA_CLE_HUB"   # même valeur que HUB_API_KEY dans .env
Invoke-RestMethod http://127.0.0.1:8003/health
Invoke-RestMethod -Headers @{ "X-Hub-Key" = $k } http://127.0.0.1:8003/metrics
```

Les routes utiles sont **sans** préfixe `/v1` (ex. `/health`, `/workflows`, …).  
Le préfixe `/v1` peut encore répondre sur certains chemins, mais ce n’est plus le contrat à documenter.

---

## Minute 12–15 — Ops optionnels

Seulement si tu as Docker / envops déjà branché :

```powershell
# Grafana stack (si tu l’utilises)
cd grafana; docker compose up -d

# Backup quotidien
python scripts/backup_daily.py
```

Sinon : saute cette étape. Le Hub local n’en a pas besoin pour démarrer.

---

## Ensuite

- [Manuel utilisateur](../guides/user-manual.md) — carte complète des écrans
- [Concepts](./concepts.md) — vocabulaire (agent, room, arbre, trust…)
- [Pipeline contenu](../guides/use-case-content-creation.md)
- [Pipeline R&D](../guides/use-case-r-d-pipeline.md)
- [Pipeline coding](../guides/use-case-coding-pipeline.md)
