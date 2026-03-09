# French Real Estate Warehouses

POC demonstrating French open data (DVF) ingestion and querying for warehouse/industrial properties.

## Architecture

- **Backend:** FastAPI (Python 3.12), single router: warehouses
- **Frontend:** Next.js (standalone mode), proxies `/api/*` to backend
- **Database:** PostgreSQL (Coolify-managed on VPS)

## Deployment (Coolify)

| Component | UUID | Domain |
|-----------|------|--------|
| API | `e4cs4cwowgws4s8sc44ssc8o` | `api-realestate.kliuiev.com` |
| Frontend | `so0c48ow4o8ss0wwsscok0ck` | `realestate.kliuiev.com` |

- Backend health: `GET /health` → `{"status": "healthy"}`
- Frontend proxies `/api/*` requests to the backend via Next.js rewrites

## Environment Variables

See `.env.example`. Required in Coolify:
- `DATABASE_URL` — PostgreSQL connection string (e.g., `postgresql://user:pass@host:5432/dbname`)

## Local Development

```bash
docker build -t frealestate . && docker run -p 8000:8000 --env-file .env frealestate
```
