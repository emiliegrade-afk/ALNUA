# Durcissement sécurité Hub — checklist VPS (H2)

Guide concret pour Emilie : verrouiller l'API ALNUA Hub en production sur un VPS.
Pas besoin d'être experte réseau — suivre les étapes dans l'ordre.

## Principe

Le Hub n'est **pas** une API publique multi-utilisateurs. C'est ton outil interne.
Objectif : seule **toi** (ou ton VPN) peux appeler l'API, avec une **clé secrète** forte.

---

## 1. Clés API — générer et séparer

1. Génère une clé maître :
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```
2. Mets-la dans `.env` sur le VPS : `HUB_API_KEY=...`
3. **Ne committe jamais** `.env` — vérifie qu'il est dans `.gitignore`.
4. Crée des clés **distinctes** par canal (optionnel mais recommandé) :
   - `HUB_API_KEY_WEB` → Vercel / Next.js
   - `HUB_API_KEY_N8N` → n8n Cloud
   - `HUB_API_KEY_MCP` → MCP Cursor
   - `HUB_API_KEY_CURSOR` → scripts locaux
5. Si une clé fuit (log, screenshot) : régénère **uniquement** celle du canal concerné.

---

## 2. Allowlist IP (`HUB_IP_ALLOWLIST`)

Sur le VPS, dans `.env` :

```
HUB_IP_ALLOWLIST=TON_IP_FIXE,IP_DU_VPN
```

- IP fixe box : regarde sur [whatismyip.com](https://whatismyip.com) depuis chez toi.
- IP VPN WireGuard/Tailscale : l'IP interne du client (ex. `100.x.x.x` Tailscale).
- **Vide en local** = OK pour dev ; **obligatoire en prod** si l'API est exposée.

Test rapide après deploy :
```bash
curl -H "X-Hub-Key: TA_CLE" https://ton-domaine/health   # doit répondre 200
curl https://ton-domaine/projects                         # doit répondre 401 (pas de clé)
```

---

## 3. VPN — ne pas exposer le Hub nu

**Recommandé** : l'API n'écoute que sur `127.0.0.1:8003` et nginx reverse-proxy + VPN.

| Option | Difficulté | Notes |
|--------|-----------|-------|
| **Tailscale** | Facile | Installe sur VPS + PC ; accès via IP Tailscale |
| **WireGuard** | Moyen | VPS + client ; très performant |
| **SSH tunnel** | Dev only | `ssh -L 8003:127.0.0.1:8003 user@vps` |

Sans VPN : au minimum `HUB_IP_ALLOWLIST` + HTTPS strict (étape 4).

---

## 4. nginx — HTTPS + reverse proxy

Exemple minimal `/etc/nginx/sites-available/alnua-hub` :

```nginx
server {
    listen 443 ssl http2;
    server_name hub.ton-domaine.fr;

    ssl_certificate     /etc/letsencrypt/live/hub.ton-domaine.fr/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hub.ton-domaine.fr/privkey.pem;

    # Bloquer tout sauf ce dont tu as besoin
    location / {
        proxy_pass http://127.0.0.1:8003;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Certificat gratuit :
```bash
sudo certbot --nginx -d hub.ton-domaine.fr
```

**Ne pas** ouvrir le port 8003 directement dans le firewall — seulement 443 (et 22 SSH restreint).

---

## 5. Firewall VPS (ufw)

```bash
sudo ufw default deny incoming
sudo ufw allow 22/tcp      # SSH — idéalement restreint à ton IP
sudo ufw allow 443/tcp      # HTTPS
sudo ufw enable
sudo ufw status
```

Avec Tailscale : tu peux **fermer 443 au public** et n'autoriser que le réseau Tailscale.

---

## 6. Secrets secondaires

| Variable | Pourquoi |
|----------|----------|
| `JWT_SECRET` | Obligatoire en prod/staging (portail beta) |
| `TELEGRAM_WEBHOOK_SECRET` | Valide les webhooks COO / Secretary |
| `SENTRY_WEBHOOK_SECRET` | Signature HMAC Sentry *(crashs apps, pas intrusion Hub)* |
| `SECURITY_AUTO_LOCKDOWN` | `1` = Hugo active lockdown localhost si finding critique |
| `SUPABASE_*`, `OPENROUTER_*` | Jamais dans le frontend public |

---

## Sentry ≠ Security Sentinel

| | **Sentry** | **Hugo — Security Sentinel** |
|--|------------|------------------------------|
| Rôle | Crashs / erreurs des apps (Naïa, etc.) | Patrouille **sécurité du Hub** |
| Détecte | Exceptions, regressions | Clé faible, `.env` dans Git, rafale 401, prod sans allowlist |
| Action | Issue / hotfix pipeline | Alerte Telegram/notify + **lockdown** optionnel |
| Endpoint | `POST /webhook/sentry` | `POST /ops/security/patrol`, `GET /ops/security/status` |

Patrouille auto toutes les **30 min** (scheduler). Lockdown actif → seules `127.0.0.1` / `::1` passent le gate IP.

```bash
# Patrouille manuelle
curl -X POST -H "X-Hub-Key: TA_CLE" http://127.0.0.1:8003/ops/security/patrol
# Lockdown manuel
curl -X POST -H "X-Hub-Key: TA_CLE" "http://127.0.0.1:8003/ops/security/lockdown?active=true&reason=test"
```

---

## 7. Vérification post-deploy

```bash
# Depuis le VPS
python scripts/verify_deploy.py

# Tests CI locaux (clés + auth + sentinel)
pytest tests/test_hub_auth.py tests/test_security_phase1.py tests/test_security_sentinel.py -q
```

Checklist rapide :

- [ ] `HUB_API_KEY` défini — l'API démarre sans erreur
- [ ] Requête sans header → `401`
- [ ] IP hors allowlist → `403` (si allowlist active)
- [ ] HTTPS actif, pas de HTTP plain
- [ ] `.env` permissions `600` : `chmod 600 .env`
- [ ] Patrouille Sentinel OK (`/ops/security/status`)

---

## 8. En cas de compromission

1. Régénère `HUB_API_KEY` + clés scopées.
2. Active le lockdown : `POST /ops/security/lockdown?active=true`.
3. Mets à jour Vercel, n8n, Cursor MCP, `.env` VPS.
4. Redémarre uvicorn / supervisor.
5. Vérifie les logs Supabase / OpenRouter pour activité anormale.
6. Documente dans `BUGS.md` si incident réel.
7. Désactive le lockdown quand c'est sécurisé : `active=false`.

---

## Références repo

- `DECISIONS.md` DEC-010 — clé obligatoire partout ; DEC-028 — clés scopées + allowlist
- `docs/api/authentication.md` — headers et clés scopées
- `agents/security_sentinel_agent.py` + `services/security_sentinel.py` — Hugo
- `BUGS.md` SEC-001 / SEC-002 — historique durcissements