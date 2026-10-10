# /alnua-devops — Docker + Deploy + CI/CD du Hub ALNUA

Patterns pour déployer, containeriser et maintenir le Hub en production.

---

## Docker — Démarrage rapide

```dockerfile
# Dockerfile (racine du repo)
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

```yaml
# docker-compose.yml
services:
  hub:
    build: .
    ports:
      - "8000:8000"
    env_file: .env
    volumes:
      - ./data:/app/data          # scores + logs persistés
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Optionnel : Redis pour cache futur
  # redis:
  #   image: redis:7-alpine
  #   ports: ["6379:6379"]
```

```bash
# Commandes quotidiennes
docker compose up -d          # démarrer en arrière-plan
docker compose logs -f hub    # logs temps réel
docker compose restart hub    # redémarrer sans rebuild
docker compose build --no-cache && docker compose up -d  # rebuild complet
```

---

## Variables d'environnement requises

```bash
# .env (ne jamais committer — .gitignore déjà configuré)
OPENROUTER_API_KEY=sk-or-...
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ...
MEM0_API_KEY=m0-...
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
HUB_API_KEY=hub_...           # pour le MCP Cursor
GITHUB_TOKEN=ghp_...          # pour le MCP GitHub
N8N_WEBHOOK_URL=https://...   # pour les triggers n8n
GODOT_PROJECT_PATH=...        # optionnel — pour godot-mcp
```

---

## Healthcheck endpoint

```python
# Déjà dans api/core.py ou api/app.py
@app.get("/health")
def health():
    return {"status": "ok", "ts": time.time()}
```

---

## Déploiement Railway / Render

```bash
# Railway CLI
railway login
railway link                  # lier au projet Railway
railway up                    # déployer

# Variables : Railway Dashboard → Variables → copier .env
```

```bash
# Render : render.yaml à la racine
services:
  - type: web
    name: alnua-hub
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn api.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - fromGroup: alnua-secrets
```

---

## GitHub Actions CI

```yaml
# .github/workflows/ci.yml
name: Hub CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -r requirements.txt
      - run: pip install pytest pytest-asyncio httpx
      - run: pytest tests/ -v --tb=short
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff
      - run: ruff check . --select=E,F,W
```

---

## Pattern de mise à jour zéro-downtime

```bash
# Sur le serveur (VPS / Railway)
git pull origin main
docker compose build hub
docker compose up -d --no-deps hub   # redémarre seulement le hub

# Vérifier que c'est up
curl http://localhost:8000/health
curl http://localhost:8000/agents/scores
```

---

## Logs & monitoring

```bash
# Logs structurés — déjà configurés via Langfuse
# Pour voir les logs locaux :
docker compose logs hub --since 1h | grep ERROR
docker compose logs hub --since 1h | grep "agent_action"

# Taille des fichiers data/
du -sh data/
ls -la data/
# Ne jamais committer data/agent_scores.json — dans .gitignore
```

---

## Commandes Hub utiles en prod

```bash
# Reset des scores (nouvelle compétition)
echo '{}' > data/agent_scores.json

# Backup des logs
cp data/cost_log.json backups/cost_log_$(date +%Y%m%d).json
cp data/event_log.json backups/event_log_$(date +%Y%m%d).json

# Test rapide des agents
curl -X POST http://localhost:8000/agents/coo/morning-brief \
  -H "Content-Type: application/json" \
  -d '{"weekly_plan": false}'
```
