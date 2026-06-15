# ALNUA Hub — Frontend (Next.js)

Dashboard and bureau UI for the ALNUA virtual company. Talks to the FastAPI backend via a same-origin proxy at `/api/hub`.

## Prerequisites

- Node.js 20+
- FastAPI backend running on port 8000 (see repo root `README` / `CLAUDE.md`)

## First-time setup

```bash
cd web
npm ci
cp .env.example .env.local
```

Edit `web/.env.local`:

| Variable | Required | Source |
|----------|----------|--------|
| `HUB_API_KEY` | **Yes** | Same value as `HUB_API_KEY` in the repo root `.env` |
| `HUB_API_BACKEND_URL` | **Yes** (local) | `http://localhost:8000` — the FastAPI origin, **not** `/api/hub` |
| `NEXT_PUBLIC_SUPABASE_URL` | Optional | Root `.env` → `SUPABASE_URL` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Optional | Root `.env` → `SUPABASE_KEY` (anon) |

If `HUB_API_KEY` is missing, every `/api/hub/*` call returns 503.

If `HUB_API_BACKEND_URL` is missing, the proxy defaults to `http://localhost:8000`.

## Development

```bash
# Terminal 1 — backend (repo root)
uvicorn api.main:app --reload --port 8000

# Terminal 2 — frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Quality checks

```bash
npx tsc --noEmit
npm run lint
npm run test:e2e   # requires backend + Playwright chromium
```

## Deploy (Vercel)

Set `HUB_API_BACKEND_URL` to the public FastAPI URL and `HUB_API_KEY` in Vercel env vars. See `deploy/vercel.env.example`.
