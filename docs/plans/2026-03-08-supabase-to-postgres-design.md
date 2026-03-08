# Migrate from Supabase to Coolify VPS Postgres

**Date:** 2026-03-08
**Status:** Approved

## Motivation

- Consolidate infrastructure: already have Postgres on VPS via Coolify
- Simplify stack: direct Postgres instead of Supabase SDK
- Cost reduction: eliminate external dependency

## Approach

SQLAlchemy ORM with async support (asyncpg driver).

## Database Connection

- **Driver:** asyncpg via SQLAlchemy[asyncio]
- **Engine:** `create_async_engine(DATABASE_URL)` with connection pooling
- **Session:** `async_sessionmaker` yielded as a FastAPI dependency
- **Env vars:** Single `DATABASE_URL` replaces 3 Supabase vars
- **Table creation:** `Base.metadata.create_all()` on startup (no migration tool)

## ORM Model

```python
class WarehouseModel(Base):
    __tablename__ = "warehouses"
    id = Column(UUID, primary_key=True, default=uuid4)
    dvf_mutation_id = Column(String, unique=True, nullable=False)
    address = Column(String)
    postal_code = Column(String)
    commune = Column(String)
    department = Column(String)
    surface_m2 = Column(Float)
    price_eur = Column(Float)
    transaction_date = Column(Date)
    latitude = Column(Float)
    longitude = Column(Float)
    property_type = Column(String)
```

## File Changes

| File | Change |
|------|--------|
| `app/db.py` | Replace Supabase clients with async engine + session factory |
| `app/models/schemas.py` | Add SQLAlchemy ORM model alongside existing Pydantic schemas |
| `app/routers/warehouses.py` | Rewrite queries to SQLAlchemy ORM |
| `app/config.py` | Replace 3 Supabase settings with `database_url` |
| `scripts/ingest_dvf.py` | Rewrite ingestion to use SQLAlchemy |
| `tests/conftest.py` | Update mocks/fixtures for SQLAlchemy |
| `tests/test_api.py` | Update to mock SQLAlchemy sessions |
| `tests/test_integration.py` | Update integration test fixtures |
| `requirements.txt` | Replace `supabase>=2.0.0` with `sqlalchemy[asyncio]>=2.0.0`, `asyncpg>=0.29.0` |
| `.env.example` | Replace Supabase vars with `DATABASE_URL` |
| `CLAUDE.md` | Update env var docs |

## Query Rewrites

- **List warehouses:** `select(WarehouseModel).order_by(desc(transaction_date)).limit().offset()`
- **Stats:** `select(func.count(), func.avg(price_eur), func.sum(surface_m2))` (moves computation to SQL)
- **Ingestion:** `session.merge()` for upsert on `dvf_mutation_id`

## What Gets Removed

- `supabase` Python SDK dependency
- Dual-key pattern (anon/service role)
- RLS dependency

## What's Preserved

- All API endpoints (same URLs, same response shapes)
- Pydantic response schemas
- Health endpoint
- Dockerfile
- Test structure (swap mocks)

## Data Strategy

Re-run DVF ingestion script against new database (no data migration needed).
