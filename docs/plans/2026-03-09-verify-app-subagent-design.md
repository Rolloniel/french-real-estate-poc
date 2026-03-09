# Verify-App Subagent Design

E2E testing skill for the French Real Estate Warehouses project, invoked as `/verify-app`. Runs smoke and functional tests against backend API and frontend UI, with a self-improvement loop to grow test coverage alongside new features.

## Invocation

```
/verify-app [smoke|full|improve] [live|local]
Defaults: smoke live
```

| Mode | Purpose |
|------|---------|
| `smoke` | Health + one hit per endpoint + pages render. Post-deploy quick check. |
| `full` | All cases from all YAML files including interactions. Pre-merge validation. |
| `improve` | Detect uncovered functionality, propose new cases, append on approval. |

| Environment | Backend | Frontend |
|-------------|---------|----------|
| `live` | `https://api-realestate.kliuiev.com` | `https://realestate.kliuiev.com` |
| `local` | Port discovery: `docker compose ps` then probe 8000-8010 | Probe 3000-3010 |

## File Structure

```
.claude/skills/verify-app/
├── SKILL.md                     # Skill definition (<500 lines)
├── cases/
│   ├── smoke.yaml               # Health + basic endpoint checks
│   ├── api-functional.yaml      # Filter combos, nearby, analytics
│   └── frontend.yaml            # Interactive UI tests
└── output/                      # GITIGNORED
    └── history.yaml             # Append-only run log
```

Gitignore additions:
```
.claude/*
!.claude/skills/
!.claude/skills/**
.claude/skills/verify-app/output/
```

## Test Case Format

### API Cases (smoke.yaml, api-functional.yaml)

Machine-readable. The skill constructs curl commands from `method` + `path`.

```yaml
- id: health-check
  phase: smoke
  method: GET
  path: /health
  assert:
    status: 200
    body_contains: "healthy"

- id: warehouses-filter-department
  phase: functional
  method: GET
  path: /api/warehouses?department=77
  assert:
    status: 200
    json_has_key: items
```

Four assertion types:
- `status` — HTTP status code
- `body_contains` — response body contains string
- `json_has_key` — JSON response has top-level key
- `json_array_not_empty` — JSON array at key is non-empty

### Frontend Cases (frontend.yaml)

Intent-driven. Natural language steps interpreted by the LLM with Playwright MCP tools. `assert` provides hard pass/fail.

```yaml
- id: map-page-renders
  phase: smoke
  description: "Navigate to home page and verify the map and filter panel load"
  steps:
    - navigate to /
    - wait for page to load
    - verify map container and filter panel are present
  assert:
    snapshot_contains: ["Filter", "Department"]

- id: filter-department-interaction
  phase: functional
  description: "Select department 77 from filter panel, verify results update"
  steps:
    - navigate to /
    - wait for map to load
    - find the department dropdown in the filter panel
    - select "77"
    - wait for results to update
    - verify the displayed data reflects the filter
  assert:
    snapshot_contains: ["77"]
```

Frontend assertion type:
- `snapshot_contains` — Playwright snapshot contains all listed strings

## Execution Flow

### Phase Order

```
Phase 1: Backend API (curl, 5s timeout per case)
  ├── smoke → phase: smoke cases from smoke.yaml
  └── full  → ALL cases from smoke.yaml + api-functional.yaml
  │
  ╰── If ALL fail → skip Phase 2 ("Backend unreachable")

Phase 2: Frontend (Playwright, 15s timeout per case)
  ├── smoke → phase: smoke cases from frontend.yaml
  └── full  → ALL cases from frontend.yaml
  │
  ╰── Load Playwright via ToolSearch
  ╰── browser_close when done

Phase 3: Results
  ├── Print pass/fail table
  └── Append run to output/history.yaml
```

### Rules

- Individual case failures do NOT stop execution — run everything, report all
- Backend all-fail → skip frontend, report "Backend unreachable"
- Local port discovery finds nothing → stop immediately
- No retries — report honest current state
- Use `browser_snapshot` only (no screenshots)

### Timeouts

- API: 5s per curl call
- Frontend: 15s per Playwright interaction sequence

## Self-Improvement Loop (improve mode)

Does not run tests. Does not modify SKILL.md. Always asks before writing.

```
Step 1: Diff Analysis (what's new)
  ├── git diff main...HEAD (or git log -10 if on main)
  ├── Extract changed files in app/routers/, app/models/, frontend/src/
  └── Build list of recently changed functionality

Step 2: Coverage Scan (what's missing)
  ├── Parse app/routers/*.py for @router.get/post → extract paths
  ├── Parse frontend/src/app/**/page.tsx → extract routes
  ├── Parse frontend/src/components/*.tsx → extract components
  ├── Load existing cases from cases/*.yaml
  └── Diff: uncovered = all_routes - covered_routes

Step 3: Propose
  ├── Merge new + gaps, deduplicate
  ├── Generate YAML cases for each
  └── Present table + full YAML to user

Step 4: User Approval
  ├── Approve all, some, or reject with feedback
  └── Approved cases appended to appropriate YAML file

Step 5: Commit
  └── "test(e2e): add cases for <summary>"
```

## Output Format

Three states: `[PASS]`, `[FAIL]`, `[SKIP]`. Failures include short reason. Phase headers group results.

```
VERIFY-APP: api-realestate.kliuiev.com (live, full)
═══════════════════════════════════════════════════════

Backend API
  [PASS] health-check
  [PASS] warehouses-list
  [FAIL] nearby-search — status 500 (expected 200)

Frontend
  [PASS] map-page-renders
  [FAIL] filter-department-interaction — snapshot missing "77" after 15s

Result: 3/5 passed, 2 failed
```

Backend-down:
```
VERIFY-APP: api-realestate.kliuiev.com (live, full)
═══════════════════════════════════════════════════════

Backend API
  [FAIL] health-check — connection refused

Backend unreachable — skipping frontend checks.

Result: 0/1 passed, 1 failed, 15 skipped
```

## History Format (output/history.yaml)

```yaml
- timestamp: 2026-03-09T14:30:00
  mode: full
  environment: live
  passed: 12
  failed: 1
  skipped: 0
  failures:
    - id: filter-department-interaction
      error: "snapshot missing '77' after 15s"
```

## Context Engineering Alignment

- **Progressive disclosure**: SKILL.md stays under 500 lines; test definitions offloaded to YAML files loaded at runtime
- **Filesystem context**: Cases are external data files, not inline in the skill
- **Context compression**: Only relevant cases loaded per mode (smoke filters by phase tag)
- **Memory system**: Append-only history.yaml tracks runs over time
- **Self-improvement**: improve mode bridges manual skill engineering and autonomous case generation
