# First 15 Minutes with ALNUA Hub

## Minute 0–3: Verify the stack

```bash
# Terminal 1 — API
uvicorn api.main:app --reload --port 8003

# Terminal 2 — Web
cd web && npm run dev
```

Open http://localhost:3000/landing — marketing page  
Open http://localhost:3000/ceo — CEO cockpit  
Check http://localhost:8003/v1/health → `{"status":"ok"}`

## Minute 3–7: Talk to your agents

1. Go to **CEO** → **Assistants**
2. Try: *"Priorités du jour"* → routes to **Aria** (COO)
3. Switch to **Nadia** → *"Rapport de la nuit Academy"*
4. Use 👍/👎 on a response — negative feedback triggers regen + Mem0 lesson

## Minute 7–10: Explore rooms

- **Open Room** — see all 9 agent rooms
- **R&D** — submit an idea, view cycle status
- **Academy** — coding exercises pipeline
- **Analytics** — agent metrics + ratings

## Minute 10–12: API & versioning

All routes exist under `/v1/*`:

```bash
curl http://localhost:8003/v1/health
curl -H "X-Hub-Key: YOUR_KEY" http://localhost:8003/v1/platform/stats
curl -H "X-Hub-Key: YOUR_KEY" http://localhost:8003/metrics
```

Multi-tenant: pass `X-Tenant-ID: alnua_coo` (or your tenant slug).

## Minute 12–15: Ops stack (optional)

```bash
# Redis + Prometheus + Grafana
cd grafana && docker compose up -d

# Grafana → http://localhost:3001 (admin/admin)
# Prometheus → http://localhost:9090

# Daily backup
python scripts/backup_daily.py

# Restore test (dry-run)
python scripts/restore_backup.py backups/YYYY-MM-DD --dry-run
```

## Next steps

- [Installation](./installation.md)
- [Concepts](./concepts.md)
- [Coding pipeline](../guides/use-case-coding-pipeline.md)
- [Content creation](../guides/use-case-content-creation.md)
- [R&D pipeline](../guides/use-case-r-d-pipeline.md)
