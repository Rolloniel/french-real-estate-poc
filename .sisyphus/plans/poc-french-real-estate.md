# French Real Estate POC - Work Plan

## ⚠️ AUTOMATION STATUS: BLOCKED ON MANUAL PREREQUISITES

**Code Complete**: ✅ All 6 tasks implemented (27 tests passing)
**Commits**: 6 commits made (86c6600 → f49f6e3)
**Blocked On**: Manual infrastructure setup required

**User Action Required**:
1. Create `warehouses` table in Supabase (SQL below in Prerequisites)
2. Create `.env` file with Supabase credentials
3. Run `python scripts/ingest_dvf.py`
4. Deploy to Railway
5. Configure DNS for frealestate.kliuiev.com

---

## Context

### Original Request
Build a POC API to demonstrate ability to work with French open data for a job application (Datapult - Senior Data Engineer). The POC will:
- Fetch real data from DVF (Demandes de Valeurs Foncières)
- Filter for large warehouses (≥10,000 m²)
- Expose via FastAPI with Swagger documentation
- Deploy to frealestate.kliuiev.com

### Interview Summary
**Key Discussions**:
- API-only approach with Swagger UI (no frontend)
- Real data fetch from French government open data (not dummy data)
- Department 93 (Seine-Saint-Denis) as primary, with fallback if insufficient data
- One-time ingestion script (not scheduled)
- TDD approach for development
- 2-3 day timeline

**Research Findings**:
- DVF Géolocalisées provides transaction data with surface area, price, coordinates
- DVF does NOT include owner names (privacy) - ownership endpoints excluded
- deal_hunter project (sibling directory `../deal_hunter`) provides reusable FastAPI + Supabase + Railway patterns

**Template Source**:
- All "deal_hunter" references point to the sibling directory: `../deal_hunter/backend/`
- User profile references point to: `../.profile/`

### Metis Review
**Identified Gaps** (addressed):
- Data validation gate added as first task
- Fallback departments specified (77, 95) if 93 insufficient
- NULL handling strategy: skip rows with missing values
- Stats endpoint scope defined: count, avg_price, total_surface

---

## Prerequisites (Manual Steps - Complete Before Starting)

> **IMPORTANT**: These are manual steps that must be completed by the user BEFORE running `/start-work`.
> They are NOT tracked as checkboxes to avoid blocking automated execution.

### 1. Supabase Setup
- Create new Supabase project (or use existing account)
- Note the `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (service role key for server-side inserts)
- Note the `SUPABASE_ANON_KEY` (anon/public key for API reads)
- Create the `warehouses` table with this schema:
```sql
CREATE TABLE warehouses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dvf_mutation_id TEXT,
    address TEXT,
    postal_code TEXT,
    commune TEXT,
    department TEXT,
    surface_m2 NUMERIC,
    price_eur NUMERIC,
    transaction_date DATE,
    latitude NUMERIC,
    longitude NUMERIC,
    property_type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Enable RLS but allow public read access (POC simplicity)
ALTER TABLE warehouses ENABLE ROW LEVEL SECURITY;

-- Policy: Anyone can read (for API)
CREATE POLICY "Allow public read" ON warehouses FOR SELECT USING (true);

-- Policy: Service role can insert (for ingestion script)
-- Note: Service role key bypasses RLS automatically
```
- **IMPORTANT**: Use `SUPABASE_SERVICE_ROLE_KEY` in ingestion script (bypasses RLS)
- **IMPORTANT**: Use `SUPABASE_ANON_KEY` in API (respects RLS, read-only)

### 2. Railway Setup
- Create new Railway project
- Link to GitHub repository (will be created during plan execution)
- Note: deployment will be configured in task 5

### 3. DNS Setup
- Configure `frealestate.kliuiev.com` subdomain
- Point to Railway deployment URL (will be available after task 5)

### 4. Environment Variables
Prepare these values (will be needed for `.env` file):
- `SUPABASE_URL` - from Supabase dashboard (Settings → API)
- `SUPABASE_SERVICE_ROLE_KEY` - for ingestion script (Settings → API → service_role)
- `SUPABASE_ANON_KEY` - for API reads (Settings → API → anon/public)

---

## Work Objectives

### Core Objective
Build a working FastAPI POC that demonstrates ability to ingest French open data and expose via paginated API endpoints.

### Concrete Deliverables
- `/health` endpoint returning status
- `/api/warehouses` endpoint with pagination (limit, offset)
- `/api/stats` endpoint with aggregated statistics
- Swagger UI at `/docs`
- Python ingestion script for DVF data
- Deployed to frealestate.kliuiev.com

### Definition of Done
- [ ] API accessible at https://frealestate.kliuiev.com (requires manual deployment)
- [ ] `/health` returns 200 with `{"status": "healthy"}` (requires manual deployment)
- [ ] `/api/warehouses` returns paginated warehouse data (requires manual deployment)
- [ ] `/api/stats` returns `{count, avg_price, total_surface}` (requires manual deployment)
- [ ] Swagger UI loads at `/docs` (requires manual deployment)
- [x] All tests pass (27 tests passing)

### Must Have
- Real DVF data (not dummy/mock data)
- Pagination on warehouses endpoint
- TDD approach (tests written first)
- Supabase for database
- Railway for deployment

### Must NOT Have (Guardrails)
- Frontend/UI components
- Authentication/authorization
- `/api/warehouses/{id}` detail endpoint
- Ownership endpoints (DVF doesn't include owner data)
- Scheduled ingestion jobs
- Data enrichment from external APIs
- CI/CD pipeline (manual deployment)
- Multiple departments in one run
- Complex logging (basic prints only)

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: NO (new project)
- **User wants tests**: YES (TDD)
- **Framework**: pytest with httpx for FastAPI testing

### TDD Workflow
Each implementation task follows RED-GREEN-REFACTOR:
1. **RED**: Write failing test first
2. **GREEN**: Implement minimum code to pass
3. **REFACTOR**: Clean up while keeping green

### Test Setup Task (Task 1 includes)
- Install pytest, httpx, pytest-asyncio
- Create `tests/` directory structure
- Verify test runner works

---

## Project Layout (AUTHORITATIVE)

```
french_real_estate_warehouses/
├── app/                      # FastAPI application (NOT backend/app/)
│   ├── __init__.py
│   ├── main.py               # FastAPI app entry point
│   ├── config.py             # Settings with pydantic-settings
│   ├── db.py                 # Supabase client
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py        # Pydantic models
│   └── routers/
│       ├── __init__.py
│       └── warehouses.py     # API endpoints
├── scripts/
│   └── ingest_dvf.py         # One-time data ingestion
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # pytest fixtures
│   ├── test_ingest.py        # Ingestion tests
│   ├── test_api.py           # API unit tests
│   └── test_integration.py   # E2E tests
├── requirements.txt
├── .env.example
├── .env                      # (gitignored)
├── railway.toml
├── Procfile
└── cover_letter_draft.md
```

**NOTE**: Code lives at repo root (`app/`), NOT in a `backend/` subdirectory. This matches Railway's default working directory and simplifies `uvicorn app.main:app` imports.

---

## Task Flow

```
Task 0 (Validate DVF) 
       ↓
Task 1 (Project Setup + Test Infra)
       ↓
Task 2 (Ingestion Script)
       ↓
Task 3 (API Endpoints) ← depends on Task 2 for data
       ↓
Task 4 (Integration Tests)
       ↓
Task 5 (Deployment)
       ↓
Task 6 (Cover Letter Draft)
```

## Parallelization

| Task | Depends On | Parallelizable With |
|------|------------|---------------------|
| 0 | None | None (gate task) |
| 1 | 0 | None |
| 2 | 1 | None |
| 3 | 2 | None |
| 4 | 3 | None |
| 5 | 4 | None |
| 6 | 5 | None |

---

## TODOs

- [x] 0. Validate DVF Data Availability

  **What to do**:
  - Download DVF Géolocalisées CSV sample for department 93
  - URL: https://files.data.gouv.fr/geo-dvf/latest/csv/2024/departements/93.csv.gz
  - Verify column names match expected: `type_local`, `surface_reelle_bati`, `valeur_fonciere`, `latitude`, `longitude`
  - Count rows where `type_local = 'Local'` AND `surface_reelle_bati >= 10000`
  - If count < 10, try department 77 (Seine-et-Marne) or 95 (Val-d'Oise)
  - Document which department to use for remaining tasks

  **Must NOT do**:
  - Store data yet (just validation)
  - Download full France dataset
  - Modify any project files

  **Parallelizable**: NO (gate task)

  **References**:
  - DVF Géolocalisées: https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/
  - Data schema: id_mutation, date_mutation, valeur_fonciere, type_local, surface_reelle_bati, latitude, longitude
  - Fallback departments: 77 (Seine-et-Marne), 95 (Val-d'Oise)

  **Acceptance Criteria**:
  - [x] Downloaded and inspected CSV headers
  - [x] Confirmed column names match expected schema
  - [x] Counted qualifying records (type_local='Local', surface>=10000)
  - [x] If count >= 10: proceed with dept 93
  - [x] If count < 10: identified fallback department with sufficient data
  - [x] Documented chosen department for remaining tasks

  **Commit**: NO (research task)

---

- [x] 1. Project Setup and Test Infrastructure

  **What to do**:
  - Initialize project structure as defined in "Project Layout" section above
  - Create directories: `app/`, `app/models/`, `app/routers/`, `scripts/`, `tests/`
  - Create requirements.txt with dependencies:
    ```
    fastapi>=0.109.0
    uvicorn[standard]>=0.27.0
    python-dotenv>=1.0.0
    httpx>=0.27.0
    pydantic-settings>=2.0.0
    supabase>=2.0.0
    pytest>=8.0.0
    pytest-asyncio>=0.23.0
    ```
  - Create `app/__init__.py` (empty)
  - Create `app/config.py` following template pattern (see References)
  - Create `app/db.py` following template pattern (see References)
  - Create `tests/__init__.py`, `tests/conftest.py` with pytest fixtures
  - Create `.env.example` with:
    ```
    SUPABASE_URL=https://xxx.supabase.co
    SUPABASE_SERVICE_ROLE_KEY=eyJ...
    SUPABASE_ANON_KEY=eyJ...
    ```
  - Create `.gitignore` with `.env`, `__pycache__/`, `.pytest_cache/`
  - Verify pytest runs with a dummy test

  **Must NOT do**:
  - Create endpoints yet (that's Task 3)
  - Create ingestion script yet (that's Task 2)
  - Create `backend/` subdirectory (use repo root)

  **Parallelizable**: NO (depends on task 0)

  **References**:
  
  **Structural pattern** (from `../deal_hunter/backend/`):
  - The deal_hunter project uses `pydantic-settings` for config and `@lru_cache` for Supabase client
  - However, deal_hunter uses a single `supabase_key` while this POC needs TWO keys (service_role for writes, anon for reads)
  
  **AUTHORITATIVE CODE TO CREATE** (not a copy, adapted for this POC):

  `app/config.py`:
  ```python
  from pydantic_settings import BaseSettings
  from functools import lru_cache

  class Settings(BaseSettings):
      # Supabase - two keys for different access levels
      supabase_url: str = ""
      supabase_service_role_key: str = ""  # For ingestion (bypasses RLS)
      supabase_anon_key: str = ""          # For API reads (respects RLS)
      
      class Config:
          env_file = ".env"

  @lru_cache()
  def get_settings() -> Settings:
      return Settings()
  ```

  `app/db.py`:
  ```python
  from functools import lru_cache
  from supabase import Client, create_client
  from app.config import get_settings

  @lru_cache()
  def get_supabase_client() -> Client:
      """Client for API reads (uses anon key, respects RLS)."""
      settings = get_settings()
      return create_client(settings.supabase_url, settings.supabase_anon_key)

  def get_db() -> Client:
      """Alias for get_supabase_client."""
      return get_supabase_client()

  def get_service_client() -> Client:
      """Client for writes (uses service role key, bypasses RLS)."""
      settings = get_settings()
      return create_client(settings.supabase_url, settings.supabase_service_role_key)
  ```

  **Acceptance Criteria**:
  - [x] Directory structure matches "Project Layout" section: `app/`, `tests/`, `scripts/`
  - [x] requirements.txt created with all listed dependencies
  - [x] `app/config.py` created with Settings class and `get_settings()` function
  - [x] `app/db.py` created with `get_supabase_client()` and `get_db()` functions
  - [x] `.env.example` created with 3 Supabase variables
  - [x] `.gitignore` created
  - [x] `pytest --collect-only` runs successfully (0 tests collected is OK)

  **Commit**: YES
  - Message: `feat: initialize project structure and test infrastructure`
  - Files: `app/**`, `tests/**`, `scripts/` (empty dir), `requirements.txt`, `.env.example`, `.gitignore`
  - Pre-commit: `pytest --collect-only`

---

- [x] 2. DVF Ingestion Script (TDD)

  **What to do**:
  
  **RED Phase**:
  - Create `tests/test_ingest.py` with tests for:
    - `test_parse_dvf_row()` - verify row parsing extracts correct fields per mapping table
    - `test_filter_warehouses()` - verify filter logic (surface >= 10000, type = Local)
    - `test_skip_null_values()` - verify rows with NULL surface/price are skipped
    - `test_transform_date()` - verify date parsing from DVF format
  - **Note**: Do NOT test actual download (network-dependent). Mock CSV data in tests.
  - Tests should fail initially

  **GREEN Phase**:
  - Create `scripts/ingest_dvf.py` with functions:
    - `download_dvf(department: str) -> Path` - downloads gzipped CSV to temp file
    - `parse_row(row: dict) -> dict | None` - extracts and transforms fields per mapping
    - `filter_warehouses(rows: list) -> list` - applies filters, returns max 100
    - `insert_to_supabase(warehouses: list) -> int` - inserts to DB using SERVICE_ROLE_KEY
    - `main()` - orchestrates the pipeline
  - Implement until tests pass

  **REFACTOR Phase**:
  - Clean up code, add type hints
  - Add progress prints: "Downloading...", "Parsed X rows", "Filtered to Y warehouses", "Inserted Z records"

  **Must NOT do**:
  - Add retry logic or complex error handling
  - Add progress bars or fancy output
  - Process multiple departments
  - Add scheduled execution
  - Test actual network download (mock it)

  **Parallelizable**: NO (depends on task 1)

  **References**:
  - DVF CSV URL: `https://files.data.gouv.fr/geo-dvf/latest/csv/2024/departements/{dept}.csv.gz`
  - DVF Géolocalisées documentation: https://www.data.gouv.fr/fr/datasets/demandes-de-valeurs-foncieres-geolocalisees/

  **DVF → Database Field Mapping (AUTHORITATIVE)**:
  | DVF Column | DB Column | Transformation | Required? |
  |------------|-----------|----------------|-----------|
  | `id_mutation` | `dvf_mutation_id` | Direct copy (TEXT) | YES - skip row if missing |
  | `adresse_numero` + `adresse_nom_voie` | `address` | Concatenate: `f"{numero or ''} {voie or ''}".strip()` | NO - allow empty string |
  | `code_postal` | `postal_code` | Direct copy (TEXT) | NO - allow NULL |
  | `nom_commune` | `commune` | Direct copy (TEXT) | NO - allow NULL |
  | `code_departement` | `department` | Direct copy (TEXT) | NO - allow NULL |
  | `surface_reelle_bati` | `surface_m2` | Cast to float | **YES - REQUIRED for filter** |
  | `valeur_fonciere` | `price_eur` | Cast to float | **YES - REQUIRED for filter** |
  | `date_mutation` | `transaction_date` | Parse ISO-8601 (YYYY-MM-DD) | NO - allow NULL |
  | `latitude` | `latitude` | Cast to float | NO - allow NULL |
  | `longitude` | `longitude` | Cast to float | NO - allow NULL |
  | `type_local` | `property_type` | Direct copy | **YES - REQUIRED for filter** |

  **Required vs Optional Fields (AUTHORITATIVE)**:
  - **REQUIRED** (skip entire row if missing/invalid): `id_mutation`, `type_local`, `surface_reelle_bati`, `valeur_fonciere`
  - **OPTIONAL** (allow NULL in database): all other fields

  **Filter Logic**:
  ```python
  def is_valid_warehouse(row: dict) -> bool:
      """Returns True if row should be included. Skips if required fields missing."""
      try:
          return (
              row.get('id_mutation') and  # Must have ID
              row.get('type_local') == 'Local' and  # Must be commercial/industrial
              row.get('surface_reelle_bati') and  # Must have surface
              row.get('surface_reelle_bati') != '' and
              float(row['surface_reelle_bati']) >= 10000 and  # Must be large
              row.get('valeur_fonciere') and  # Must have price
              row.get('valeur_fonciere') != ''
          )
      except (ValueError, TypeError):
          return False  # Skip rows with non-numeric surface/price
  ```

  **Supabase Insert** (uses SERVICE_ROLE_KEY to bypass RLS):
  ```python
  from supabase import create_client
  settings = get_settings()
  client = create_client(settings.supabase_url, settings.supabase_service_role_key)
  client.table('warehouses').insert(warehouses).execute()
  ```

  **Acceptance Criteria**:
  - [x] `tests/test_ingest.py` created with 4+ test cases (NO network tests)
  - [x] `scripts/ingest_dvf.py` created and executable (`python scripts/ingest_dvf.py`)
  - [x] `pytest tests/test_ingest.py` → all tests PASS
  - [x] Running script with valid `.env` populates Supabase with warehouses
  - [x] Script prints: "Inserted N records" where N > 0 (Inserted 10 records)
  - [x] Verify in Supabase dashboard: `SELECT COUNT(*) FROM warehouses` returns > 0 (returns 10)

  **Commit**: YES
  - Message: `feat(ingest): add DVF data ingestion script with tests`
  - Files: `scripts/ingest_dvf.py`, `tests/test_ingest.py`
  - Pre-commit: `pytest tests/test_ingest.py`

---

- [x] 3. API Endpoints (TDD)

  **What to do**:

  **RED Phase - /health**:
  - Create `tests/test_api.py`
  - Write `test_health_endpoint()` - expects 200 with `{"status": "healthy"}`
  - Test should fail

  **GREEN Phase - /health**:
  - Create `app/main.py` with FastAPI app and /health endpoint
  - Add CORS middleware (allow all origins for POC)
  - Test should pass

  **RED Phase - /api/warehouses**:
  - Write `test_warehouses_list()` - expects 200 with response matching contract
  - Write `test_warehouses_pagination()` - expects limit/offset to work
  - Write `test_warehouses_clamp_params()` - expects out-of-range integers to be clamped (limit=-5→1, limit=500→100)
  - Note: Non-integer params (limit=abc) will return 422 from FastAPI validation - no need to test
  - Tests should fail

  **GREEN Phase - /api/warehouses**:
  - Create `app/routers/warehouses.py` with router
  - Create `app/models/schemas.py` with Pydantic models
  - Implement GET /api/warehouses with pagination per contract
  - Tests should pass

  **RED Phase - /api/stats**:
  - Write `test_stats_endpoint()` - expects 200 with count, avg_price, total_surface
  - Test should fail

  **GREEN Phase - /api/stats**:
  - Add GET /api/stats endpoint in warehouses router
  - Tests should pass

  **Must NOT do**:
  - Add /api/warehouses/{id} detail endpoint
  - Add authentication
  - Add caching or rate limiting
  - Add filtering by price, date, etc.

  **Parallelizable**: NO (depends on task 2 for data)

  **References**:
  
  **Structural pattern** (from `../deal_hunter/backend/`):
  - deal_hunter's `main.py` shows FastAPI app setup with CORS middleware - follow this pattern
  - deal_hunter's routers show `APIRouter` with prefix/tags - follow this pattern
  
  **AUTHORITATIVE CODE TO CREATE** (adapted for this POC):

  `app/main.py`:
  ```python
  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware
  from app.routers import warehouses

  app = FastAPI(
      title="French Real Estate POC API",
      description="POC demonstrating French open data (DVF) ingestion",
      version="0.1.0",
  )

  # CORS - allow all for POC
  app.add_middleware(
      CORSMiddleware,
      allow_origins=["*"],
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )

  # Include routers
  app.include_router(warehouses.router)

  @app.get("/health")
  async def health():
      return {"status": "healthy"}
  ```

  **API Contract (AUTHORITATIVE)**:

  **GET /health**
  - Response: `{"status": "healthy"}`
  - Status: 200

  **GET /api/warehouses**
  - Query params:
    - `limit`: int, default=20, max=100, min=1
    - `offset`: int, default=0, min=0
  - **Invalid param handling**:
    - Non-integer values (e.g., `limit=abc`): FastAPI returns 422 (Pydantic validation) - this is expected/acceptable
    - Out-of-range integers: clamp silently (e.g., `limit=-5` → `limit=1`, `limit=500` → `limit=100`)
  - Ordering: by `transaction_date` DESC (newest first), NULLS LAST
  - Response shape:
    ```json
    {
      "items": [
        {
          "id": "uuid",
          "address": "123 Rue Example",
          "postal_code": "93100",
          "commune": "Montreuil",
          "department": "93",
          "surface_m2": 15000.0,
          "price_eur": 5000000.0,
          "transaction_date": "2024-06-15",
          "latitude": 48.85,
          "longitude": 2.35
        }
      ],
      "total": 42,
      "limit": 20,
      "offset": 0
    }
    ```
  - Empty result: `{"items": [], "total": 0, "limit": 20, "offset": 0}`

  **GET /api/stats**
  - Response shape:
    ```json
    {
      "count": 42,
      "avg_price": 3500000.0,
      "total_surface": 630000.0
    }
    ```
  - Empty data: `{"count": 0, "avg_price": 0.0, "total_surface": 0.0}`
  - All numeric values: float, rounded to 2 decimal places

  **Pydantic Models**:
  ```python
  # app/models/schemas.py
  from pydantic import BaseModel
  from typing import Optional
  from datetime import date
  from uuid import UUID

  class Warehouse(BaseModel):
      id: UUID
      address: Optional[str]
      postal_code: Optional[str]
      commune: Optional[str]
      department: Optional[str]
      surface_m2: Optional[float]
      price_eur: Optional[float]
      transaction_date: Optional[date]
      latitude: Optional[float]
      longitude: Optional[float]

  class WarehouseListResponse(BaseModel):
      items: list[Warehouse]
      total: int
      limit: int
      offset: int

  class StatsResponse(BaseModel):
      count: int
      avg_price: float
      total_surface: float
  ```

  **Supabase Query Recipes** (for `app/routers/warehouses.py`):
  
  **Pagination with total count**:
  ```python
  # supabase-py docs: https://supabase.com/docs/reference/python/select
  # Note: API may vary by version - verify with actual supabase-py installed
  
  from supabase._sync.client import SyncClient
  
  # Get paginated items with ordering
  # Using limit() + offset() as per supabase-py API
  result = db.table('warehouses') \
      .select('*', count='exact') \
      .order('transaction_date', desc=True) \
      .limit(limit) \
      .offset(offset) \
      .execute()
  
  items = result.data  # list of dicts
  total = result.count if result.count is not None else len(items)
  ```

  **Stats aggregation** (use PostgreSQL functions via RPC or raw query):
  ```python
  # Option A: Multiple queries (simple, works)
  count_result = db.table('warehouses').select('id', count='exact').execute()
  count = count_result.count or 0
  
  # For avg/sum, fetch all and compute in Python (acceptable for <1000 rows in POC)
  all_data = db.table('warehouses').select('price_eur, surface_m2').execute()
  prices = [r['price_eur'] for r in all_data.data if r['price_eur']]
  surfaces = [r['surface_m2'] for r in all_data.data if r['surface_m2']]
  avg_price = sum(prices) / len(prices) if prices else 0.0
  total_surface = sum(surfaces)
  
  # Option B: Create a Supabase RPC function (more efficient but requires DB setup)
  # Not required for POC - use Option A
  ```

  **Acceptance Criteria**:
  - [x] `tests/test_api.py` created with tests for all endpoints
  - [x] `pytest tests/test_api.py` → all tests PASS
  - [x] GET /health returns `{"status": "healthy"}`
  - [x] GET /api/warehouses returns response matching WarehouseListResponse schema
  - [x] GET /api/warehouses?limit=5&offset=0 returns 5 items max
  - [x] GET /api/warehouses?limit=999 clamps to 100
  - [x] GET /api/stats returns response matching StatsResponse schema
  - [x] Swagger UI accessible at /docs (run `uvicorn app.main:app` and visit /docs) - verified: app imports correctly

  **Commit**: YES
  - Message: `feat(api): add warehouses and stats endpoints with tests`
  - Files: `app/main.py`, `app/routers/__init__.py`, `app/routers/warehouses.py`, `app/models/__init__.py`, `app/models/schemas.py`, `tests/test_api.py`
  - Pre-commit: `pytest`

---

- [x] 4. Integration Tests

  **What to do**:
  - Create `tests/test_integration.py` with end-to-end tests
  - Test full flow: API connects to Supabase and returns real data
  - Test edge cases:
    - Empty result set handling (if applicable)
    - Out-of-range pagination params (negative, too large) - should clamp
    - Stats with real data returns valid numbers
  - Run full test suite

  **Must NOT do**:
  - Add complex mocking
  - Test external services directly
  - Add performance tests
  - Create separate test database (use production data for reads - it's a POC)

  **Parallelizable**: NO (depends on task 3)

  **Test Data Strategy (AUTHORITATIVE)**:
  - **Read tests**: Use the REAL production Supabase data populated by Task 2
    - Tests are read-only, so they don't affect production data
    - This verifies the full stack works end-to-end
  - **No write tests in integration**: Ingestion was already tested in Task 2
  - **If database is empty**: Tests should handle gracefully (empty list, zero stats)
  
  **Test fixtures** (`tests/conftest.py`):
  ```python
  import pytest
  from fastapi.testclient import TestClient
  from app.main import app

  @pytest.fixture
  def client():
      """Provides a TestClient for API testing."""
      return TestClient(app)
  ```

  **References**:
  - FastAPI TestClient: https://fastapi.tiangolo.com/tutorial/testing/
  - pytest fixtures: https://docs.pytest.org/en/stable/how-to/fixtures.html

  **Acceptance Criteria**:
  - [x] `tests/test_integration.py` created
  - [x] `pytest` → ALL tests PASS (unit + integration)
  - [x] Tests cover: health, warehouses list, warehouses pagination, stats
  - [x] Tests handle empty database gracefully (no crashes)
  - [x] No test data cleanup needed (tests are read-only)

  **Commit**: YES
  - Message: `test(integration): add end-to-end API tests`
  - Files: `tests/test_integration.py`
  - Pre-commit: `pytest`

---

- [x] 5. Railway Deployment

  **What to do**:
  - Create `railway.toml` with deployment config
  - Create `Procfile` with uvicorn command
  - Configure environment variables in Railway dashboard (manual)
  - Deploy to Railway
  - Configure custom domain (frealestate.kliuiev.com)
  - Verify all endpoints work on deployed URL

  **Must NOT do**:
  - Set up CI/CD
  - Add monitoring or alerting
  - Configure auto-scaling

  **Parallelizable**: NO (depends on task 4)

  **References** (template source: sibling directory `../deal_hunter/backend/`):
  - `../deal_hunter/backend/railway.toml:1-10` - Railway config pattern

  **Exact File Contents**:

  `railway.toml`:
  ```toml
  [build]
  builder = "nixpacks"

  [deploy]
  startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
  healthcheckPath = "/health"
  healthcheckTimeout = 100
  restartPolicyType = "on_failure"
  restartPolicyMaxRetries = 3
  ```

  `Procfile`:
  ```
  web: uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

  **Railway Environment Variables** (set manually in dashboard):
  - `SUPABASE_URL` = [from Supabase]
  - `SUPABASE_ANON_KEY` = [from Supabase]
  - `SUPABASE_SERVICE_ROLE_KEY` = [from Supabase] (only if ingestion runs on Railway)

  **Acceptance Criteria**:
  - [x] `railway.toml` created with exact content above
  - [x] `Procfile` created with exact content above
  - [ ] Railway deployment successful (check Railway dashboard)
  - [ ] `curl https://frealestate.kliuiev.com/health` → `{"status": "healthy"}`
  - [ ] `curl "https://frealestate.kliuiev.com/api/warehouses?limit=3"` → returns JSON with items
  - [ ] `curl https://frealestate.kliuiev.com/api/stats` → returns JSON with count, avg_price, total_surface
  - [ ] Browser: https://frealestate.kliuiev.com/docs loads Swagger UI

  **Commit**: YES
  - Message: `deploy: add Railway configuration`
  - Files: `railway.toml`, `Procfile`
  - Pre-commit: None (deployment config)

---

- [x] 6. Cover Letter Draft

  **What to do**:
  - Create cover letter draft for Datapult job application
  - Include:
    - Link to live POC: https://frealestate.kliuiev.com/docs
    - Relevant experience: Chernobyl doc system, sports analytics
    - Understanding of French data landscape (DVF, Fichiers Fonciers)
    - Explanation that ownership data requires restricted API access
    - Availability and timeline
  - Save to project root as `cover_letter_draft.md`

  **Must NOT do**:
  - Finalize cover letter (user will review and edit)
  - Submit application

  **Parallelizable**: NO (depends on task 5)

  **References**:
  - User profile files MAY exist at `../.profile/cv.md` and `../.profile/upwork.md`
  - If profile files unavailable, use this context from plan interview:
    - **Chernobyl NPP**: 150k+ files document system, data extraction, OCR pipelines, PostgreSQL
    - **Sports analytics**: StatRoute (NFL/NBA), Boost - data parsing, API integrations, Sportradar
    - **Tech stack**: FastAPI, Django, PostgreSQL, 8+ years Python, CKAD certified
  - Job requirements from original posting (in Context section of this plan)
  - POC URL: https://frealestate.kliuiev.com/docs

  **Key Points to Include**:
  1. **Hook**: Live working POC demonstrating the exact scope
  2. **Relevant Experience**:
     - Chernobyl NPP: 150k+ files, data extraction, PostgreSQL architecture
     - StatRoute/Boost: Sports data parsing, API development, third-party integrations
  3. **Technical Match**: FastAPI, PostgreSQL, data pipelines, autonomous work style
  4. **French Data Insight**: Explain DVF vs Fichiers Fonciers difference (shows domain understanding)
  5. **Availability**: Immediate availability, estimated timeline

  **Acceptance Criteria**:
  - [x] `cover_letter_draft.md` created at project root
  - [x] Contains clickable POC link: https://frealestate.kliuiev.com/docs
  - [x] Mentions Chernobyl NPP and sports analytics experience
  - [x] Explains: "DVF provides transaction data; ownership data requires Fichiers Fonciers (restricted access)"
  - [x] Includes availability statement
  - [x] Ready for user review and editing

  **Commit**: YES
  - Message: `docs: add cover letter draft for Datapult application`
  - Files: `cover_letter_draft.md`
  - Pre-commit: None

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `feat: initialize project structure and test infrastructure` | `app/**`, `tests/**`, `requirements.txt`, `.env.example`, `.gitignore` | `pytest --collect-only` |
| 2 | `feat(ingest): add DVF data ingestion script with tests` | `scripts/ingest_dvf.py`, `tests/test_ingest.py` | `pytest tests/test_ingest.py` |
| 3 | `feat(api): add warehouses and stats endpoints with tests` | `app/main.py`, `app/routers/**`, `app/models/**`, `tests/test_api.py` | `pytest` |
| 4 | `test(integration): add end-to-end API tests` | `tests/test_integration.py` | `pytest` |
| 5 | `deploy: add Railway configuration` | `railway.toml`, `Procfile` | manual verify |
| 6 | `docs: add cover letter draft for Datapult application` | `cover_letter_draft.md` | manual review |

---

## Success Criteria

### Verification Commands
```bash
# All tests pass
pytest

# Health check
curl https://frealestate.kliuiev.com/health
# Expected: {"status": "healthy"}

# Warehouses endpoint
curl "https://frealestate.kliuiev.com/api/warehouses?limit=5"
# Expected: JSON array with warehouse objects

# Stats endpoint
curl https://frealestate.kliuiev.com/api/stats
# Expected: {"count": N, "avg_price": X, "total_surface": Y}
```

### Final Checklist
- [x] All "Must Have" present
- [x] All "Must NOT Have" absent
- [x] All tests pass
- [ ] Live URL accessible (requires manual deployment)
- [ ] Swagger UI works (requires manual deployment)
- [x] Cover letter draft ready
