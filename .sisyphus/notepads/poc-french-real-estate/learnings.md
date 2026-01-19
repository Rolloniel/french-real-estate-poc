# POC French Real Estate - Learnings

## 2026-01-19 Task 0: DVF Data Validation

**Department chosen**: 77 (Seine-et-Marne)
**Qualifying records found**: 15
**Column verification**: PASS

### Validation Results

| Department | Name | Qualifying Records | Status |
|------------|------|-------------------|--------|
| 93 | Seine-Saint-Denis | 7 | FAIL (< 10) |
| 77 | Seine-et-Marne | 15 | PASS (>= 10) |

### Schema Verification

All expected columns confirmed present in DVF Geolocalisees dataset:
- `id_mutation` - unique transaction ID
- `date_mutation` - transaction date  
- `valeur_fonciere` - price in EUR
- `type_local` - property type
- `surface_reelle_bati` - built surface in m²
- `latitude`, `longitude` - coordinates

### Key Discovery: type_local Values

The task specification mentioned filtering by `type_local = 'Local'`, but the actual value in the dataset is:
```
'Local industriel. commercial ou assimilé'
```

Full distribution of `type_local` values (dept 93):
- `'Dépendance'`: 21,293
- `'Appartement'`: 15,745
- `(empty)`: 8,870
- `'Maison'`: 3,790
- `'Local industriel. commercial ou assimilé'`: 1,366

### Sample Qualifying Records from Dept 77

| Commune | Surface (m²) | Price (EUR) | Coordinates |
|---------|-------------|-------------|-------------|
| Vaux-le-Pénil | 16,070 | 4,000,000 | (48.530, 2.688) |
| Marolles-sur-Seine | 37,503 | 39,379,116 | (48.377, 3.025) |
| Vert-Saint-Denis | 37,856 | 38,689,704 | (48.572, 2.638) |
| Torcy | 93,011 | 1 | (48.857, 2.651) |
| Coulommiers | 43,168 | - | (48.829, 3.096) |

### Notes

1. **Data Quality**: Some records have missing `valeur_fonciere` (price) or show nominal values like 1 EUR (likely corporate transfers or special transactions)
2. **Coordinates**: Most records have geocoded coordinates, but some are missing
3. **Data Source**: https://files.data.gouv.fr/geo-dvf/latest/csv/2024/departements/77.csv.gz
4. **File Size**: ~11MB uncompressed

### Recommendation

**Proceed with Department 77 (Seine-et-Marne)** for all remaining POC tasks.

This department has sufficient large commercial/industrial properties (15 records >= 10,000 m²) and is part of the Île-de-France region with good logistics infrastructure (warehouses, distribution centers).

---

## 2026-01-19 Task 1: Project Setup and Test Infrastructure

### Created Structure

```
french_real_estate_warehouses/
├── app/
│   ├── __init__.py          (empty)
│   ├── config.py             (Settings class with Supabase config)
│   ├── db.py                 (Supabase clients: anon + service role)
│   ├── models/
│   │   └── __init__.py       (empty)
│   └── routers/
│       └── __init__.py       (empty)
├── scripts/                   (empty dir for ingestion script)
├── tests/
│   ├── __init__.py           (empty)
│   └── conftest.py           (pytest fixtures placeholder)
├── requirements.txt           (8 dependencies)
├── .env.example               (3 Supabase variables)
└── .gitignore                 (standard Python ignores)
```

### Dependencies (requirements.txt)

- fastapi>=0.109.0
- uvicorn[standard]>=0.27.0
- python-dotenv>=1.0.0
- httpx>=0.27.0
- pydantic-settings>=2.0.0
- supabase>=2.0.0
- pytest>=8.0.0
- pytest-asyncio>=0.23.0

### Key Design Decisions

1. **Two Supabase clients**: 
   - `get_supabase_client()` / `get_db()`: Uses anon key, respects RLS (for API reads)
   - `get_service_client()`: Uses service role key, bypasses RLS (for ingestion)

2. **Configuration**: Uses `pydantic-settings` with `.env` file support and `@lru_cache()` for singleton pattern

3. **Test fixture**: Placeholder `client` fixture in conftest.py, will be completed in Task 3 when main.py exists

### Verification

```bash
$ pytest --collect-only
============================= test session starts ==============================
platform linux -- Python 3.12.6, pytest-9.0.2
collected 0 items
========================= no tests collected in 0.02s =========================
```

✅ Pytest runs successfully (0 tests expected at this stage)

---

## 2026-01-19 Task 2: DVF Ingestion Script (TDD)

### Created Files

1. **tests/test_ingest.py** - 11 test cases covering:
   - `TestParseRow`: Field extraction, address handling, missing id_mutation
   - `TestFilterWarehouses`: Surface filter, type_local filter, 100 record limit
   - `TestSkipNullValues`: Null surface, null price, missing id_mutation
   - `TestTransformDate`: ISO format parsing, empty date handling

2. **scripts/ingest_dvf.py** - Complete ingestion pipeline with:
   - `download_dvf(department)`: Downloads gzipped CSV, decompresses to temp file
   - `parse_row(row)`: Transforms DVF row to DB schema
   - `filter_warehouses(rows)`: Applies filters, returns max 100 records
   - `insert_to_supabase(warehouses)`: Inserts using service role client
   - `main(department)`: Orchestrates pipeline with progress prints

3. **scripts/__init__.py** - Package marker for imports

### Key Implementation Details

1. **Filter Logic** (exact from task spec):
   - `type_local == 'Local industriel. commercial ou assimilé'` (exact match)
   - `surface_reelle_bati >= 10000` (m²)
   - `valeur_fonciere` must be non-empty
   - `id_mutation` must be present

2. **Field Mapping** (DVF → DB):
   - `id_mutation` → `dvf_mutation_id`
   - `adresse_numero` + `adresse_nom_voie` → `address` (concatenated)
   - `surface_reelle_bati` → `surface_m2` (float)
   - `valeur_fonciere` → `price_eur` (float)
   - `date_mutation` → `transaction_date` (ISO-8601 string)
   - `type_local` → `property_type`

3. **Progress Output**:
   ```
   Downloading DVF data for department 77...
   Parsing CSV...
   Parsed X rows
   Filtered to Y warehouses
   Inserted Z records
   ```

### Test Results

```bash
$ uv run pytest tests/test_ingest.py -v
======================= 11 passed, 14 warnings in 0.48s ========================
```

### Usage

```bash
# Run ingestion (requires .env with Supabase credentials)
uv run python -m scripts.ingest_dvf
```

### Notes

1. **No venv on Synology NAS**: Symlinks not supported, use `uv run` instead
2. **Pyright clean**: 0 errors, 0 warnings
3. **TDD workflow**: RED (tests first) → GREEN (implementation) → REFACTOR (type hints)

---

## 2026-01-19 Task 3: API Endpoints (TDD)

### Created Files

1. **tests/test_api.py** - 6 test cases with mocked Supabase:
   - `TestHealthEndpoint`: test_health_returns_200
   - `TestWarehousesEndpoint`: test_warehouses_list_returns_200, test_warehouses_pagination, test_warehouses_clamp_limit_max, test_warehouses_clamp_limit_min
   - `TestStatsEndpoint`: test_stats_returns_200

2. **app/models/schemas.py** - Pydantic models:
   - `Warehouse`: id, address, postal_code, commune, department, surface_m2, price_eur, transaction_date, latitude, longitude
   - `WarehouseListResponse`: items, total, limit, offset
   - `StatsResponse`: count, avg_price, total_surface

3. **app/routers/warehouses.py** - API router with:
   - `GET /api/warehouses`: Paginated list with clamping (limit: 1-100, offset: >=0)
   - `GET /api/stats`: Aggregate stats (count, avg_price, total_surface)

4. **app/main.py** - FastAPI app with:
   - CORS middleware (allow all for POC)
   - `/health` endpoint
   - Warehouses router included

5. **tests/conftest.py** - Updated with working client fixture

### Key Implementation Details

1. **Pagination Clamping** (silent, not validation error):
   - `limit = max(1, min(100, limit))` - clamps to [1, 100]
   - `offset = max(0, offset)` - clamps to >= 0
   - FastAPI Query constraints would reject, we clamp instead

2. **Test Mocking Strategy**:
   - Mock `app.db.get_db` and `app.db.get_supabase_client`
   - Return MagicMock with chained method calls
   - Sample data with 2 warehouses for realistic testing

3. **Stats Calculation**:
   - Count via `count='exact'` on select
   - Avg/sum calculated in Python (acceptable for POC <1000 rows)
   - Rounded to 2 decimal places

### API Contract

| Endpoint | Method | Response |
|----------|--------|----------|
| `/health` | GET | `{"status": "healthy"}` |
| `/api/warehouses` | GET | `{items: [...], total: N, limit: N, offset: N}` |
| `/api/stats` | GET | `{count: N, avg_price: N.NN, total_surface: N.NN}` |

### Test Results

```bash
$ pytest tests/test_api.py -v
======================== 6 passed, 13 warnings in 0.25s ========================
```

### Notes

1. **Venv workaround**: Created venv in `/tmp/french_real_estate_venv` due to Synology NAS symlink issues
2. **LSP errors**: Pyright shows import errors due to venv location, but code is correct
3. **TDD workflow**: RED (tests first with mocks) → GREEN (implementation) → VERIFY (all pass)

---

## 2026-01-19 Task 4: Integration Tests

### Created Files

1. **tests/test_integration.py** - 10 integration test cases:
   - `TestIntegrationHealth`: test_health_endpoint_returns_healthy_status
   - `TestIntegrationWarehouses`: 5 tests covering response structure, pagination, large offset, negative limit clamping, excessive limit clamping
   - `TestIntegrationStats`: 2 tests covering response structure and non-negative values
   - `TestIntegrationEmptyDatabase`: 2 tests for empty database handling (warehouses + stats)

### Test Coverage Summary

| Test File | Tests | Purpose |
|-----------|-------|---------|
| test_api.py | 6 | Unit tests for API endpoints |
| test_ingest.py | 11 | Unit tests for ingestion script |
| test_integration.py | 10 | Integration tests for full stack |
| **Total** | **27** | All passing |

### Key Implementation Details

1. **Integration Test Strategy**:
   - Still uses mocked Supabase (can't guarantee real data in CI)
   - Tests full request/response flow through FastAPI
   - Verifies response structure, types, and edge cases

2. **Empty Database Handling**:
   - Separate fixture `empty_db_client` with empty mock data
   - Warehouses returns `{items: [], total: 0, ...}`
   - Stats returns `{count: 0, avg_price: 0.0, total_surface: 0.0}`

3. **Edge Cases Tested**:
   - Large offset (10000) - doesn't crash
   - Negative limit (-10) - clamped to 1
   - Excessive limit (500) - clamped to 100

### Test Results

```bash
$ pytest -v
======================== 27 passed, 14 warnings in 0.20s ========================
```

### Notes

1. **Read-only tests**: All tests are read-only, no cleanup needed
2. **Mocking pattern**: Consistent with test_api.py, uses nested MagicMock for Supabase chain
3. **Warnings**: 14 deprecation warnings from pyiceberg/pydantic (not our code)

---

## 2026-01-19 Task 5: Railway Deployment

### Created Files

1. **railway.toml** - Railway deployment configuration:
   - Builder: nixpacks
   - Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Health check: `/health` with 100s timeout
   - Restart policy: on_failure with max 3 retries

2. **Procfile** - Heroku-compatible process file:
   - `web: uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Commit

```
1b30035 deploy: add Railway configuration
```

---

## 2026-01-19 Task 6: Cover Letter Draft

### Created Files

1. **cover_letter_draft.md** - Complete cover letter with:
   - Live POC link: https://frealestate.kliuiev.com/docs
   - Chernobyl NPP experience (150k+ files, PostgreSQL, OCR)
   - Sports analytics experience (StatRoute, Boost, NFL/NBA, Sportradar)
   - DVF vs Fichiers Fonciers explanation
   - Availability statement (immediate, CET timezone)
   - Contact information

### Commit

```
f49f6e3 docs: add cover letter draft for Datapult application
```

---

## BLOCKED ITEMS (Require Manual User Action)

The following items cannot be automated and require user intervention:

### 1. Supabase Setup
- Create Supabase project
- Run SQL to create `warehouses` table (schema in plan Prerequisites)
- Get credentials: SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY

### 2. Environment Configuration
- Create `.env` file from `.env.example`
- Add real Supabase credentials

### 3. Data Ingestion
- Run: `python scripts/ingest_dvf.py`
- Requires valid `.env` with Supabase credentials
- Expected output: "Inserted N records" where N > 0

### 4. Railway Deployment
- Link GitHub repository to Railway
- Set environment variables in Railway dashboard
- Deploy

### 5. DNS Configuration
- Point `frealestate.kliuiev.com` to Railway deployment URL

### 6. Live Verification
- `curl https://frealestate.kliuiev.com/health`
- `curl https://frealestate.kliuiev.com/api/warehouses?limit=3`
- `curl https://frealestate.kliuiev.com/api/stats`
- Browser: https://frealestate.kliuiev.com/docs

---

## Summary

| Task | Status | Commit |
|------|--------|--------|
| 0. DVF Validation | ✅ Complete | (research) |
| 1. Project Setup | ✅ Complete | `86c6600` |
| 2. Ingestion Script | ✅ Complete | `2c3166a` |
| 3. API Endpoints | ✅ Complete | `1c9f6fc` |
| 4. Integration Tests | ✅ Complete | `ab24c4a` |
| 5. Railway Config | ✅ Complete | `1b30035` |
| 6. Cover Letter | ✅ Complete | `f49f6e3` |

**All CODE tasks complete. 27 tests passing.**

---

## 2026-01-19 Ingestion Executed Successfully

**User completed manual prerequisites:**
- ✅ Created Supabase project
- ✅ Created `warehouses` table
- ✅ Configured `.env` with credentials

**Ingestion results:**
```
Downloading DVF data for department 77...
Parsing CSV...
Parsed 62813 rows
Filtered to 10 warehouses
Inserted 10 records
```

**Data verified in Supabase:**
- Total records: 10
- Sample: Vaux-le-Pénil (16,070 m², €4M), Marolles-sur-Seine (37,503 m², €39M)

**API tested with real data:**
- Health: 200 OK
- Warehouses: 10 total, pagination works
- Stats: count=10, avg_price=€9,421,162, total_surface=314,765 m²

**Remaining:** Railway deployment + DNS configuration
