# API — Authentication

## Hub API Key
Toutes les routes protégées exigent :
```
X-Hub-Key: <HUB_API_KEY>
```

En développement, si `HUB_API_KEY` est vide, l'API est ouverte (warning log).

## Multi-tenant
```
X-Tenant-ID: alnua_coo
```
Défaut : `DEFAULT_TENANT_ID` dans `.env`.

## Beta portal (JWT)
Routes `/beta/feedback` utilisent le JWT testeur, pas la hub key.

## Versioning
Préférer les routes `/v1/*` pour intégrations externes.
