# Verify-App Subagent Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Create a `/verify-app` Claude Code skill that runs e2e tests against the French Real Estate Warehouses backend API and frontend, with a self-improvement mode that detects uncovered functionality and proposes new test cases.

**Architecture:** Claude Code skill (SKILL.md + YAML case files) stored in `.claude/skills/verify-app/`. The skill reads test case definitions from YAML files at runtime. API checks use curl via Bash. Frontend checks use Playwright MCP tools. An `improve` mode scans the codebase for uncovered routes/pages and proposes new YAML cases.

**Tech Stack:** Claude Code skill (Markdown), YAML test case files, Bash/curl (API), Playwright MCP (frontend)

**Design doc:** `docs/plans/2026-03-09-verify-app-subagent-design.md`

---

### Task 1: Gitignore & Directory Scaffolding

**Files:**
- Modify: `.gitignore`
- Create: `.claude/skills/verify-app/cases/` (directory)
- Create: `.claude/skills/verify-app/output/.gitkeep`

**Step 1: Update .gitignore to allow `.claude/skills/` while ignoring output**

Replace the existing `.claude/` line in `.gitignore` with:

```gitignore
.claude/*
!.claude/skills/
!.claude/skills/**
.claude/skills/verify-app/output/
```

This commits skills + cases but ignores the mutable run history output directory.

**Step 2: Create the directory structure**

```bash
mkdir -p .claude/skills/verify-app/cases
mkdir -p .claude/skills/verify-app/output
touch .claude/skills/verify-app/output/.gitkeep
```

**Step 3: Verify structure**

```bash
find .claude/skills -type f
```

Expected:
```
.claude/skills/verify-app/output/.gitkeep
```

**Step 4: Commit**

```bash
git add .gitignore .claude/skills/verify-app/output/.gitkeep
git commit -m "chore: scaffold verify-app skill directory structure"
```

---

### Task 2: Smoke Test Cases (smoke.yaml)

**Files:**
- Create: `.claude/skills/verify-app/cases/smoke.yaml`

**Context:** The backend has these endpoints (from `app/main.py`, `app/routers/warehouses.py`, `app/routers/analytics.py`):
- `GET /health` — returns `{"status": "healthy"}`
- `GET /api/warehouses` — returns `{"items": [...], "total": N, "limit": N, "offset": N}`
- `GET /api/warehouses/nearby?lat=...&lng=...` — returns `{"items": [...], "total": N, ...}`
- `GET /api/departments` — returns `["77", "78", ...]`
- `GET /api/stats` — returns `{"count": N, "avg_price": N, "total_surface": N}`
- `GET /api/analytics/price-per-m2` — returns `{"buckets": [...], "median": N, "mean": N}`
- `GET /api/analytics/by-department` — returns `{"departments": [...]}`
- `GET /api/analytics/price-trends` — returns `{"trends": [...]}`
- `GET /api/analytics/top-communes` — returns `{"most_expensive": [...], "cheapest": [...]}`
- `GET /api/analytics/department-stats` — returns `{"items": [...]}`

**Step 1: Write smoke.yaml with one case per endpoint**

```yaml
# Smoke test cases — one hit per endpoint to verify the app is up and responding.
# Used by: /verify-app smoke (default mode)

- id: health-check
  phase: smoke
  method: GET
  path: /health
  assert:
    status: 200
    body_contains: "healthy"

- id: warehouses-list
  phase: smoke
  method: GET
  path: /api/warehouses?limit=5
  assert:
    status: 200
    json_has_key: items

- id: nearby-search
  phase: smoke
  method: GET
  path: /api/warehouses/nearby?lat=48.8566&lng=2.3522&radius_km=100
  assert:
    status: 200
    json_has_key: items

- id: departments-list
  phase: smoke
  method: GET
  path: /api/departments
  assert:
    status: 200

- id: stats-global
  phase: smoke
  method: GET
  path: /api/stats
  assert:
    status: 200
    json_has_key: count

- id: analytics-price-per-m2
  phase: smoke
  method: GET
  path: /api/analytics/price-per-m2
  assert:
    status: 200
    json_has_key: buckets

- id: analytics-by-department
  phase: smoke
  method: GET
  path: /api/analytics/by-department
  assert:
    status: 200
    json_has_key: departments

- id: analytics-price-trends
  phase: smoke
  method: GET
  path: /api/analytics/price-trends
  assert:
    status: 200
    json_has_key: trends

- id: analytics-top-communes
  phase: smoke
  method: GET
  path: /api/analytics/top-communes
  assert:
    status: 200
    json_has_key: most_expensive

- id: analytics-department-stats
  phase: smoke
  method: GET
  path: /api/analytics/department-stats
  assert:
    status: 200
    json_has_key: items
```

**Step 2: Verify YAML is valid**

```bash
python3 -c "import yaml; yaml.safe_load(open('.claude/skills/verify-app/cases/smoke.yaml')); print('Valid YAML')"
```

Expected: `Valid YAML`

**Step 3: Commit**

```bash
git add .claude/skills/verify-app/cases/smoke.yaml
git commit -m "test(e2e): add smoke test cases for all API endpoints"
```

---

### Task 3: Functional API Test Cases (api-functional.yaml)

**Files:**
- Create: `.claude/skills/verify-app/cases/api-functional.yaml`

**Context:** These test deeper functionality — filter combinations, parameter validation, response content checks. Only run in `full` mode.

**Step 1: Write api-functional.yaml**

```yaml
# Functional API test cases — deeper endpoint validation.
# Used by: /verify-app full

- id: warehouses-filter-department
  phase: functional
  method: GET
  path: /api/warehouses?department=77&limit=5
  assert:
    status: 200
    json_has_key: items

- id: warehouses-filter-price-range
  phase: functional
  method: GET
  path: /api/warehouses?min_price=100000&max_price=5000000&limit=5
  assert:
    status: 200
    json_has_key: items

- id: warehouses-filter-surface-range
  phase: functional
  method: GET
  path: /api/warehouses?min_surface=10000&max_surface=50000&limit=5
  assert:
    status: 200
    json_has_key: items

- id: warehouses-filter-commune
  phase: functional
  method: GET
  path: /api/warehouses?commune=paris&limit=5
  assert:
    status: 200
    json_has_key: items

- id: warehouses-filter-combined
  phase: functional
  method: GET
  path: /api/warehouses?department=77&min_surface=10000&limit=5
  assert:
    status: 200
    json_has_key: items

- id: warehouses-pagination
  phase: functional
  method: GET
  path: /api/warehouses?limit=2&offset=0
  assert:
    status: 200
    json_has_key: total

- id: nearby-small-radius
  phase: functional
  method: GET
  path: /api/warehouses/nearby?lat=48.8566&lng=2.3522&radius_km=10
  assert:
    status: 200
    json_has_key: items

- id: analytics-price-per-m2-has-stats
  phase: functional
  method: GET
  path: /api/analytics/price-per-m2
  assert:
    status: 200
    json_has_key: median

- id: analytics-by-department-has-data
  phase: functional
  method: GET
  path: /api/analytics/by-department
  assert:
    status: 200
    json_array_not_empty: departments

- id: analytics-trends-has-data
  phase: functional
  method: GET
  path: /api/analytics/price-trends
  assert:
    status: 200
    json_array_not_empty: trends

- id: analytics-top-communes-has-both
  phase: functional
  method: GET
  path: /api/analytics/top-communes
  assert:
    status: 200
    json_has_key: cheapest

- id: analytics-department-stats-has-data
  phase: functional
  method: GET
  path: /api/analytics/department-stats
  assert:
    status: 200
    json_array_not_empty: items
```

**Step 2: Verify YAML is valid**

```bash
python3 -c "import yaml; yaml.safe_load(open('.claude/skills/verify-app/cases/api-functional.yaml')); print('Valid YAML')"
```

Expected: `Valid YAML`

**Step 3: Commit**

```bash
git add .claude/skills/verify-app/cases/api-functional.yaml
git commit -m "test(e2e): add functional API test cases for filters, pagination, analytics"
```

---

### Task 4: Frontend Test Cases (frontend.yaml)

**Files:**
- Create: `.claude/skills/verify-app/cases/frontend.yaml`

**Context:** The frontend has two pages:
- `/` — Map page with header ("Warehouse Map", "France DVF"), NavTabs ("Map", "Analytics"), StatsBar ("Warehouses", "Avg. Price", "Total Surface"), FilterPanel (department dropdown, commune search, price/surface ranges, date ranges), and a Leaflet map
- `/analytics` — Analytics page with header ("Warehouse Analytics"), same NavTabs/StatsBar, and AnalyticsDashboard with 4 chart cards: "Price per m2 Distribution", "Average Price per m2 by Department", "Price Trends Over Time", "Top Communes by Price per m2"

The FilterPanel has: a "Filters" heading, "Department" label with `<select>` (options: "All departments" + department codes), "Commune" with text input (placeholder "Search commune..."), "Price (EUR)" with Min/Max inputs, "Surface (m2)" with Min/Max inputs, "Transaction Date" with two date inputs. It also shows a result count (`N results`).

**Step 1: Write frontend.yaml**

```yaml
# Frontend test cases — page rendering and interactive UI checks.
# Smoke cases verify pages load. Functional cases test interactions.
# Used by: /verify-app smoke (smoke phase only), /verify-app full (all phases)

# --- Smoke: pages render ---

- id: map-page-renders
  phase: smoke
  description: "Navigate to home page, verify the map page header, navigation, and filter panel load"
  steps:
    - navigate to /
    - wait for page to load
    - take a snapshot
    - verify header shows "Warehouse Map" and navigation tabs "Map" and "Analytics" are present
    - verify filter panel is visible with "Filters" heading and "Department" label
  assert:
    snapshot_contains: ["Warehouse Map", "Map", "Analytics", "Filters", "Department"]

- id: analytics-page-renders
  phase: smoke
  description: "Navigate to analytics page, verify header and chart titles load"
  steps:
    - navigate to /analytics
    - wait for page to load (charts may take a moment)
    - take a snapshot
    - verify header shows "Warehouse Analytics"
    - verify at least one chart card title is visible
  assert:
    snapshot_contains: ["Warehouse Analytics", "Price per m2"]

# --- Functional: interactions ---

- id: nav-map-to-analytics
  phase: functional
  description: "Click the Analytics tab from the map page, verify navigation works"
  steps:
    - navigate to /
    - wait for page to load
    - find and click the "Analytics" navigation tab/link
    - wait for analytics page to load
    - verify the page now shows "Warehouse Analytics" header
  assert:
    snapshot_contains: ["Warehouse Analytics"]

- id: nav-analytics-to-map
  phase: functional
  description: "Click the Map tab from the analytics page, verify navigation back works"
  steps:
    - navigate to /analytics
    - wait for page to load
    - find and click the "Map" navigation tab/link
    - wait for map page to load
    - verify the page now shows "Warehouse Map" header
  assert:
    snapshot_contains: ["Warehouse Map"]

- id: filter-department-interaction
  phase: functional
  description: "On map page, select a department from the filter dropdown, verify the result count changes"
  steps:
    - navigate to /
    - wait for page to load and note the initial result count shown in the filter panel
    - find the department select dropdown (below "Department" label)
    - select a specific department value (pick one from the dropdown options, e.g. the first non-empty option)
    - wait 2-3 seconds for results to update
    - take a snapshot
    - verify the result count has changed or the department value is reflected in the dropdown
  assert:
    snapshot_contains: ["results"]

- id: filter-commune-search
  phase: functional
  description: "On map page, type a commune name in the search input, verify results update"
  steps:
    - navigate to /
    - wait for page to load
    - find the commune text input (placeholder "Search commune...")
    - type a commune name that likely exists (e.g. "Roissy" or "Meaux")
    - wait 2-3 seconds for results to update
    - take a snapshot
    - verify the input now contains the typed text
  assert:
    snapshot_contains: ["results"]

- id: stats-bar-displays
  phase: functional
  description: "Verify the stats bar in the header shows warehouse count, avg price, and total surface"
  steps:
    - navigate to /
    - wait for page to load and for stats to fetch
    - take a snapshot
    - verify the header area contains "Warehouses", "Avg. Price", and "Total Surface" labels
  assert:
    snapshot_contains: ["Warehouses", "Avg. Price", "Total Surface"]

- id: analytics-charts-load
  phase: functional
  description: "Verify all four chart cards render on the analytics page"
  steps:
    - navigate to /analytics
    - wait for page to fully load (all charts)
    - take a snapshot
    - verify all chart card titles are visible
  assert:
    snapshot_contains: ["Price per m2 Distribution", "Average Price per m2 by Department", "Price Trends Over Time", "Top Communes"]

- id: analytics-summary-stats
  phase: functional
  description: "Verify the summary stats row shows median, mean, departments count, and time periods"
  steps:
    - navigate to /analytics
    - wait for page to fully load
    - take a snapshot
    - verify summary stat labels are present
  assert:
    snapshot_contains: ["Median Price/m2", "Mean Price/m2", "Departments", "Time Periods"]
```

**Step 2: Verify YAML is valid**

```bash
python3 -c "import yaml; yaml.safe_load(open('.claude/skills/verify-app/cases/frontend.yaml')); print('Valid YAML')"
```

Expected: `Valid YAML`

**Step 3: Commit**

```bash
git add .claude/skills/verify-app/cases/frontend.yaml
git commit -m "test(e2e): add frontend test cases for page renders and interactions"
```

---

### Task 5: SKILL.md — Smoke & Full Modes

**Files:**
- Create: `.claude/skills/verify-app/SKILL.md`

**Context:** This is the main skill file. It must stay under 500 lines (context engineering). It references the deal_hunter verify-app skill as a template (see `~/projects/personal/side-projects/deal_hunter/.claude/skills/verify-app/SKILL.md`). Key differences: no auth flows, multiple YAML case files instead of hardcoded checks, three modes.

The SKILL.md is instructions for the LLM — it describes what to do when the skill is invoked. It is NOT executable code.

**Step 1: Write SKILL.md with argument parsing, environment setup, smoke/full execution, and output format**

```markdown
---
name: verify-app
description: >-
  E2E smoke and functional tests for French Real Estate Warehouses.
  Validates backend API endpoints and frontend UI against live or local.
  Supports smoke (quick), full (deep), and improve (self-improvement) modes.
argument-hint: "[smoke|full|improve] [live|local]"
metadata:
  author: rolloniel
  version: 1.0.0
  category: testing
  tags: [e2e, smoke-test, functional-test, verification]
---

# Verify-App: French Real Estate Warehouses E2E Tests

Run e2e tests against the backend API and frontend. Three modes: smoke (quick health check), full (all test cases including interactions), improve (detect and propose new test cases).

## Arguments

- `/verify-app` — Defaults to `smoke live`
- `/verify-app smoke [live|local]` — Quick: health + one hit per endpoint + pages render
- `/verify-app full [live|local]` — Deep: all cases from all YAML files including frontend interactions
- `/verify-app improve` — Scan codebase for uncovered functionality, propose new YAML cases

## Instructions

Parse arguments. First arg is mode (`smoke`, `full`, or `improve`), second is environment (`live` or `local`). Both are optional with defaults `smoke` and `live`. Arguments can appear in any order — if you see `live` or `local` as the first arg, treat it as the environment with mode defaulting to `smoke`.

If mode is `improve`, skip to the **Improve Mode** section below.

### Environment Setup

**Live mode:**
```
BACKEND_URL = https://api-realestate.kliuiev.com
FRONTEND_URL = https://realestate.kliuiev.com
```

**Local mode:**
1. Try default ports: `http://localhost:8000` (backend) and `http://localhost:3000` (frontend)
2. Run `curl -s --max-time 2 http://localhost:8000/health` — if it fails, run discovery:
   a. Run `docker compose ps` in the project directory to find container port mappings
   b. If no containers, probe ports 8000-8010 for backend (`/health` endpoint) and 3000-3010 for frontend (HTTP 200)
   c. If nothing found, output "No local services detected" and stop
3. Use discovered URLs for the rest of the run

### Loading Test Cases

Read the YAML case files from the skill's `cases/` directory:

- **smoke mode:** Read `cases/smoke.yaml` and `cases/frontend.yaml`. Only run cases where `phase: smoke`.
- **full mode:** Read ALL files: `cases/smoke.yaml`, `cases/api-functional.yaml`, `cases/frontend.yaml`. Run ALL cases regardless of phase.

The case files are located relative to this skill at `.claude/skills/verify-app/cases/`.

### Phase 1: Backend API Checks

For each API test case (from `smoke.yaml` and `api-functional.yaml`), run:

```bash
curl -s --max-time 5 "${BACKEND_URL}${case.path}"
```

Evaluate assertions:
- `status: N` — Check HTTP status code. Use `curl -s -o /dev/null -w "%{http_code}" --max-time 5` to get the status, then a separate call to get the body.
- `body_contains: "text"` — Response body contains the string
- `json_has_key: key` — Parse response as JSON, check top-level key exists
- `json_array_not_empty: key` — Parse as JSON, check the key's value is a non-empty array

Mark each case as `[PASS]` or `[FAIL]` (with reason).

**Early stopping:** If ALL Phase 1 cases fail, skip Phase 2 entirely. Output "Backend unreachable — skipping frontend checks."

### Phase 2: Frontend Checks

**IMPORTANT:** Load Playwright MCP tools before using them. Use ToolSearch with `select:` prefix to load each tool:
- `select:mcp__playwright__browser_navigate`
- `select:mcp__playwright__browser_snapshot`
- `select:mcp__playwright__browser_click`
- `select:mcp__playwright__browser_fill_form`
- `select:mcp__playwright__browser_select_option`
- `select:mcp__playwright__browser_press_key`
- `select:mcp__playwright__browser_wait_for`
- `select:mcp__playwright__browser_close`

For each frontend test case (from `frontend.yaml`):

1. Follow the natural-language `steps` using Playwright MCP tools
2. After completing steps, take a `browser_snapshot`
3. Check `snapshot_contains` — the snapshot text must contain ALL listed strings
4. Mark as `[PASS]` or `[FAIL]` (with reason like "snapshot missing 'X' after 15s")

**Timeout:** 15 seconds per frontend case. If steps take longer, mark as `[FAIL]` with timeout reason.

**When done:** Call `browser_close` to clean up.

### Phase 3: Results

Output the report in this exact format:

```
VERIFY-APP: {domain} ({environment}, {mode})
═══════════════════════════════════════════════════════

Backend API
  [{STATUS}] {case.id}
  [{STATUS}] {case.id}
  ...

Frontend
  [{STATUS}] {case.id}
  [{STATUS}] {case.id}
  ...

Result: {passed}/{total} passed{, {failed} failed}{, {skipped} skipped}
```

Where `{STATUS}` is `PASS`, `FAIL`, or `SKIP`. For `FAIL`, append reason after ` — `. For local mode, add discovered URLs below the header.

### Append to History

After outputting results, append a run entry to `.claude/skills/verify-app/output/history.yaml`:

```yaml
- timestamp: {ISO 8601 now}
  mode: {smoke|full}
  environment: {live|local}
  passed: {N}
  failed: {N}
  skipped: {N}
  failures:
    - id: {case.id}
      error: "{reason}"
```

Create the file if it doesn't exist. Use the Bash tool to append (read existing content first if file exists, then write the updated content).

---

## Improve Mode

When invoked with `/verify-app improve`, do NOT run any tests. Instead, analyze the codebase to find uncovered functionality and propose new test cases.

### Step 1: Diff Analysis (what's new)

Check what has changed recently:

```bash
# If on a feature branch:
git diff main...HEAD --name-only
# If on main:
git log --oneline -10
git diff HEAD~10 --name-only
```

Filter for files in:
- `app/routers/*.py` — backend endpoint changes
- `app/models/schemas.py` — new response schemas
- `frontend/src/app/**` — new pages
- `frontend/src/components/**` — new/modified components

For each changed router file, read it and extract new/modified `@router.get` or `@router.post` decorators with their paths.

### Step 2: Coverage Scan (what's missing)

Read all existing case files from `.claude/skills/verify-app/cases/`:
- `smoke.yaml`
- `api-functional.yaml`
- `frontend.yaml`

Extract the set of `path` values (API cases) and `description` summaries (frontend cases) that are already covered.

Then scan the codebase for ALL routes:

**Backend:** Read `app/routers/warehouses.py` and `app/routers/analytics.py`. Extract every `@router.get(...)` and `@router.post(...)` path. Cross-reference with existing API case paths.

**Frontend:** Read `frontend/src/app/**/page.tsx` files to find all page routes. Read `frontend/src/components/*.tsx` to find key interactive components. Cross-reference with existing frontend case descriptions.

Compute: `uncovered = all_routes - covered_routes`

### Step 3: Propose New Cases

For each uncovered route or component:
1. Generate a YAML test case following the format in the existing case files
2. Assign `phase: functional` (new cases are always functional, not smoke)
3. For API cases: choose sensible query parameters based on the endpoint's signature
4. For frontend cases: write natural-language steps describing the interaction

Present to the user in a table:

```
NEW CASES PROPOSED ({N}):
┌──────────────────────────┬──────────────────────┬────────────────────────┐
│ ID                       │ File                 │ Reason                 │
├──────────────────────────┼──────────────────────┼────────────────────────┤
│ {case-id}                │ {target-yaml-file}   │ {uncovered/new/changed}│
└──────────────────────────┴──────────────────────┴────────────────────────┘
```

Then show the full YAML for each proposed case.

### Step 4: User Approval

Ask the user to review. They can:
- **Approve all** — append all proposed cases to their target files
- **Approve some** — specify which cases to keep by ID
- **Reject with feedback** — modify and re-propose

### Step 5: Commit

After appending approved cases, commit:

```bash
git add .claude/skills/verify-app/cases/
git commit -m "test(e2e): add cases for {brief summary of what was added}"
```

---

## Rules

- No retries — report honest current state
- 5-second timeout for curl, 15-second timeout for Playwright interactions
- Use `browser_snapshot` only — no screenshots
- Do NOT modify this SKILL.md in improve mode — only modify case YAML files
- Close the browser when done using `browser_close`
- If an unexpected error occurs, mark that check as `[FAIL]` with the error message and continue
```

**Step 2: Count lines to verify under 500**

```bash
wc -l .claude/skills/verify-app/SKILL.md
```

Expected: under 500 lines.

**Step 3: Commit**

```bash
git add .claude/skills/verify-app/SKILL.md
git commit -m "feat: add verify-app e2e testing skill with smoke, full, and improve modes"
```

---

### Task 6: Update CLAUDE.md with Verification Section

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Add verification section to CLAUDE.md**

Append after the "Local Development" section:

```markdown

## Verification

Run e2e tests with the verify-app skill:

```
/verify-app              # smoke test against live (default)
/verify-app full live    # full test suite against live
/verify-app smoke local  # smoke test against local dev
/verify-app full local   # full test suite against local dev
/verify-app improve      # detect uncovered functionality, propose new test cases
```

Test cases live in `.claude/skills/verify-app/cases/` (YAML). Run history in `.claude/skills/verify-app/output/history.yaml` (gitignored).
```

**Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add verification section to CLAUDE.md"
```

---

### Task 7: Validate — Run Smoke Test Against Live

**Step 1: Invoke the skill against live**

Run `/verify-app smoke live` to validate the skill works end-to-end.

**Step 2: Review output**

Verify:
- All API smoke cases produce `[PASS]` or reasonable `[FAIL]` results
- Frontend smoke cases load pages and find expected text
- Output format matches the design spec
- History file was created at `.claude/skills/verify-app/output/history.yaml`

**Step 3: If any issues, fix the relevant YAML case or SKILL.md and re-run**

Fix assertions that don't match actual responses (e.g., different key names, missing text in snapshots). Update the YAML files and commit fixes:

```bash
git add .claude/skills/verify-app/
git commit -m "fix(e2e): adjust assertions to match actual app responses"
```

---

### Task 8: Validate — Run Full Test Against Live

**Step 1: Invoke the skill in full mode**

Run `/verify-app full live` to validate all functional cases work.

**Step 2: Review output**

Verify:
- Functional API cases (filters, pagination, analytics) pass
- Frontend interaction cases (nav, filters, stats bar, charts) pass
- No false positives or false negatives

**Step 3: Fix any failing cases and commit**

```bash
git add .claude/skills/verify-app/
git commit -m "fix(e2e): adjust functional test assertions after live validation"
```

---

### Task 9: Validate — Run Improve Mode

**Step 1: Invoke improve mode**

Run `/verify-app improve` to validate the self-improvement loop.

**Step 2: Review output**

Verify:
- The skill correctly identifies all backend routes from `app/routers/`
- The skill correctly identifies frontend pages and components
- It cross-references against existing YAML cases
- If any gaps exist, it proposes reasonable new cases
- If no gaps exist, it reports full coverage

**Step 3: If it proposes cases, review and approve/reject to verify the append workflow works**

**Step 4: Commit any accepted cases**

```bash
git add .claude/skills/verify-app/cases/
git commit -m "test(e2e): add cases from improve mode validation"
```
