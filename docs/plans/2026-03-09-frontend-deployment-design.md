# Frontend Deployment Design

## Context

The project has a Next.js frontend that needs deploying to Coolify alongside the existing FastAPI backend. Both should be accessible via `realestate.kliuiev.com`, with path-based routing handled by Next.js server-side rewrites.

## Architecture

```
Browser -> realestate.kliuiev.com (Traefik/SSL)
            -> Frontend (Next.js, port 3000)
               /* -> serves Next.js pages
               /api/* -> rewrites to backend (internal Docker network)

Browser -> api-realestate.kliuiev.com (Traefik/SSL)
            -> Backend (FastAPI, port 8000)
               /api/* -> warehouse & analytics endpoints
               /health -> health check
               /docs -> Swagger UI
```

## Approach: Next.js as Gateway (Two Coolify Apps)

Next.js already rewrites `/api/*` to `BACKEND_URL` in `next.config.ts`. The frontend becomes the public-facing app, proxying API calls to the backend over the internal Docker network.

### Changes Required

1. **Update existing backend Coolify app** - change FQDN from `realestate.kliuiev.com` to `api-realestate.kliuiev.com`
2. **Create new frontend Coolify app** - same GitHub repo, `base_directory: /frontend`, `dockerfile_location: /Dockerfile`, FQDN `realestate.kliuiev.com`, port 3000
3. **Set frontend env var** - `BACKEND_URL=http://<backend-container-name>:8000` (internal Docker network)
4. **Frontend health check** - ensure Next.js responds on `/` for Coolify health checks

### What Stays the Same

- Backend code (no changes)
- Frontend code (no changes, rewrites already configured)
- Database (unchanged)
- Auto-deploy on push to main (both apps trigger from same repo)

### DNS

Wildcard `*.kliuiev.com` already resolves to VPS (212.227.108.5). No DNS changes needed.
