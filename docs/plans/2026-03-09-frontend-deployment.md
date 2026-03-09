# Frontend Deployment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deploy the Next.js frontend to Coolify alongside the existing FastAPI backend, both accessible via `realestate.kliuiev.com` with path-based routing.

**Architecture:** Next.js serves as the public gateway at `realestate.kliuiev.com`, proxying `/api/*` requests to the FastAPI backend over the internal Docker network. Backend remains publicly accessible at `api-realestate.kliuiev.com` for direct API access/Swagger.

**Tech Stack:** Coolify API, Traefik, Docker, Next.js rewrites

---

### Task 1: Update Backend FQDN

Change the existing backend Coolify app from `realestate.kliuiev.com` to `api-realestate.kliuiev.com`.

**Step 1: Update FQDN via Coolify API**

```bash
export COOLIFY_API_TOKEN=$(grep COOLIFY_API_TOKEN ~/projects/personal/.env | cut -d'=' -f2)

curl -s -X PATCH \
  -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"domains": "https://api-realestate.kliuiev.com"}' \
  https://coolify.kliuiev.com/api/v1/applications/e4cs4cwowgws4s8sc44ssc8o
```

Expected: 200 OK with updated app config showing new FQDN.

Note: The API field might be `fqdn` instead of `domains`. If the first attempt fails, try `{"fqdn": "https://api-realestate.kliuiev.com"}`.

**Step 2: Restart backend to apply new Traefik labels**

```bash
curl -s -X POST \
  -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  https://coolify.kliuiev.com/api/v1/applications/e4cs4cwowgws4s8sc44ssc8o/restart
```

**Step 3: Verify backend is accessible at new FQDN**

```bash
curl -s https://api-realestate.kliuiev.com/health
```

Expected: `{"status": "healthy"}`

Also verify old URL no longer serves:
```bash
curl -s -o /dev/null -w "%{http_code}" https://realestate.kliuiev.com/health
```

Expected: 404 or connection error (Traefik no longer routes to backend).

---

### Task 2: Create Frontend Coolify App

Create a new Coolify application for the Next.js frontend in the same project.

**Step 1: Create application via Coolify API**

```bash
curl -s -X POST \
  -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_uuid": "hk0gw4coskcowk4csgkowk4g",
    "environment_name": "production",
    "server_uuid": "l8wwkk8w008w4ggcgoo4o0ck",
    "destination_uuid": "fsg8kw8w4gk8cs0c040gko84",
    "type": "public",
    "name": "french-real-estate-frontend",
    "description": "Next.js frontend for French Real Estate Warehouses",
    "git_repository": "Rolloniel/french-real-estate-poc",
    "git_branch": "main",
    "build_pack": "dockerfile",
    "ports_exposes": "3000",
    "base_directory": "/frontend",
    "dockerfile_location": "/Dockerfile",
    "domains": "https://realestate.kliuiev.com"
  }' \
  https://coolify.kliuiev.com/api/v1/applications
```

Expected: 201 Created with new app UUID.

Note: If this endpoint format doesn't work, use the Coolify UI via Playwright as fallback. The API field names may vary — try `git_repository` vs `repository`, `domains` vs `fqdn`, etc.

**Step 2: Save the new app UUID**

Record the UUID from the response — needed for subsequent API calls.

---

### Task 3: Configure Frontend Environment Variables

The Next.js rewrites compile `BACKEND_URL` at build time. We need it as a build-time env var pointing to the backend container on the Docker network.

The backend container hostname in Coolify is its UUID: `e4cs4cwowgws4s8sc44ssc8o`.

**Step 1: Set BACKEND_URL as build-time env var**

```bash
FRONTEND_UUID="<uuid-from-task-2>"

curl -s -X POST \
  -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"key":"BACKEND_URL","value":"http://e4cs4cwowgws4s8sc44ssc8o:8000","is_build_time":true}' \
  https://coolify.kliuiev.com/api/v1/applications/$FRONTEND_UUID/envs
```

Expected: 201 Created.

**Step 2: Verify env var was set**

```bash
curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  https://coolify.kliuiev.com/api/v1/applications/$FRONTEND_UUID/envs
```

Expected: List includes `BACKEND_URL` with `is_build_time: true`.

---

### Task 4: Deploy Frontend and Verify

**Step 1: Trigger deployment**

```bash
curl -s -X POST \
  -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  https://coolify.kliuiev.com/api/v1/applications/$FRONTEND_UUID/deploy
```

Note: The deploy endpoint might be `/deploy`, `/start`, or `/restart`. Try in that order.

**Step 2: Wait for deployment and check logs**

```bash
# Check deployment status/logs
curl -s -H "Authorization: Bearer $COOLIFY_API_TOKEN" \
  https://coolify.kliuiev.com/api/v1/applications/$FRONTEND_UUID/logs
```

Wait for the build to complete (Next.js build takes ~1-2 minutes).

**Step 3: Verify frontend serves pages**

```bash
curl -s -o /dev/null -w "%{http_code}" https://realestate.kliuiev.com/
```

Expected: 200

**Step 4: Verify API proxy works end-to-end**

```bash
curl -s https://realestate.kliuiev.com/api/health
```

Expected: `{"status": "healthy"}` (proxied through Next.js to FastAPI)

```bash
curl -s "https://realestate.kliuiev.com/api/stats" | python3 -m json.tool
```

Expected: JSON with warehouse stats.

**Step 5: Verify direct backend access still works**

```bash
curl -s https://api-realestate.kliuiev.com/docs
```

Expected: Swagger UI HTML.

---

### Task 5: Update Project Documentation

**Step 1: Update CLAUDE.md**

Add the frontend app UUID to the deployment table and update the domain info.

**Files:**
- Modify: `CLAUDE.md`

Update the deployment table:

```markdown
## Deployment (Coolify)

| Component | UUID | Domain |
|-----------|------|--------|
| API | `e4cs4cwowgws4s8sc44ssc8o` | `api-realestate.kliuiev.com` |
| Frontend | `<new-uuid>` | `realestate.kliuiev.com` |
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add frontend Coolify deployment details"
```
