# API — Authentication

## Hub API Key (obligatoire — DEC-010)

`HUB_API_KEY` est **obligatoire dans tous les environnements**, y compris en local.
L'API refuse de démarrer si la clé est absente (`config/settings.py::_validate_security`).
Il n'existe **plus** de mode dev ouvert.

Toutes les routes protégées exigent le header :

```
X-Hub-Key: <votre-clé>
```

Réponse `401` si la clé est absente ou invalide.

## Clés scopées par canal (optionnel)

En plus de la clé maître `HUB_API_KEY`, vous pouvez définir des clés dédiées par intégration.
Chaque clé non vide est acceptée avec les mêmes droits que la clé maître — utile pour
rotation ou révocation par canal sans changer toutes les intégrations.

| Variable `.env` | Usage typique |
|-----------------|---------------|
| `HUB_API_KEY` | Clé maître (obligatoire) |
| `HUB_API_KEY_WEB` | Proxy Next.js (`web/.env.local`) |
| `HUB_API_KEY_N8N` | Workflows n8n Cloud |
| `HUB_API_KEY_MCP` | Serveur MCP Hub |
| `HUB_API_KEY_CURSOR` | Cursor / agents locaux |

Génération recommandée :

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Allowlist IP (optionnel)

Variable `HUB_IP_ALLOWLIST` — liste d'adresses IP séparées par des virgules (match exact, pas de CIDR pour l'instant).

- **Vide** (défaut) : toutes les IP sont acceptées (pratique en local).
- **Renseignée** : seules les IP listées passent ; les autres reçoivent `403`.

Exemple production derrière VPN :

```
HUB_IP_ALLOWLIST=10.8.0.2,203.0.113.50
```

## Routes exemptées (sans `X-Hub-Key`)

- `GET /health`, `GET /metrics`
- Webhooks : `POST /webhook/telegram`, `POST /webhook/telegram/secretary`, `POST /webhook/sentry`
- Portails publics beta, waitlist, partnerships, assets R&D publics, redirects `/go/*`

Ces routes ont leur propre auth (secret Telegram, signature Sentry, JWT testeur, etc.).

## Multi-tenant

```
X-Tenant-ID: alnua_coo
```

Défaut : `DEFAULT_TENANT_ID` dans `.env`.

## Beta portal (JWT)

Routes `/beta/feedback` utilisent le JWT testeur, pas la hub key.

## Versioning

Préférer les routes `/v1/*` pour intégrations externes.
