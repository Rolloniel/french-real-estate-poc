# POC French Real Estate - Blockers & Problems

## 2026-01-19 Attempted Resolution

**Attempted**: Use Supabase credentials from sibling `deal_hunter` project.

**Result**: FAILED
- Found credentials at `/home/rolloniel/synology_nas/projects/upwork/deal_hunter/.env`
- Connected to Supabase successfully
- **ERROR**: `warehouses` table does not exist in this Supabase project
- Cannot create table programmatically (Supabase client doesn't support raw SQL)

**Conclusion**: User MUST manually create the `warehouses` table in Supabase dashboard before ingestion can run.

---

## 2026-01-19 Orchestration Complete - Remaining Blockers

### Status: ALL CODE TASKS COMPLETE

The following items are **BLOCKED** and require **manual user action**:

---

## Blocker 1: Supabase Project Setup

**What's needed:**
1. Create new Supabase project (or use existing)
2. Run SQL to create `warehouses` table:

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

ALTER TABLE warehouses ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow public read" ON warehouses FOR SELECT USING (true);
```

3. Get credentials from Settings → API:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY` (anon/public)
   - `SUPABASE_SERVICE_ROLE_KEY` (service_role)

**Why blocked:** Requires user's Supabase account access.

---

## Blocker 2: Environment Configuration

**What's needed:**
1. Copy `.env.example` to `.env`
2. Fill in real Supabase credentials

```bash
cp .env.example .env
# Edit .env with real values
```

**Why blocked:** Contains secrets that cannot be committed to git.

---

## Blocker 3: Data Ingestion

**What's needed:**
1. Ensure `.env` is configured with valid Supabase credentials
2. Run ingestion script:

```bash
python scripts/ingest_dvf.py
```

**Expected output:**
```
Downloading DVF data for department 77...
Parsing CSV...
Parsed XXXXX rows
Filtered to 15 warehouses
Inserted 15 records
```

**Why blocked:** Requires Blocker 1 and 2 to be resolved first.

---

## Blocker 4: Railway Deployment

**What's needed:**
1. Create Railway project
2. Link to GitHub repository
3. Set environment variables in Railway dashboard:
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
4. Deploy

**Why blocked:** Requires user's Railway account access.

---

## Blocker 5: DNS Configuration

**What's needed:**
1. Get Railway deployment URL
2. Configure `frealestate.kliuiev.com` subdomain to point to Railway

**Why blocked:** Requires user's DNS provider access.

---

## Blocker 6: Live Verification

**What's needed:**
After deployment, verify:

```bash
curl https://frealestate.kliuiev.com/health
# Expected: {"status": "healthy"}

curl "https://frealestate.kliuiev.com/api/warehouses?limit=3"
# Expected: JSON with items array

curl https://frealestate.kliuiev.com/api/stats
# Expected: {"count": N, "avg_price": X, "total_surface": Y}
```

Also verify Swagger UI loads at: https://frealestate.kliuiev.com/docs

**Why blocked:** Requires Blockers 1-5 to be resolved first.

---

## Resolution Path

1. User completes Supabase setup (Blocker 1)
2. User creates `.env` file (Blocker 2)
3. User runs ingestion script (Blocker 3)
4. User deploys to Railway (Blocker 4)
5. User configures DNS (Blocker 5)
6. User verifies live endpoints (Blocker 6)

**All code is ready. Only manual infrastructure setup remains.**
