# Supabase to Postgres Migration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace Supabase SDK with SQLAlchemy ORM connecting to Coolify VPS PostgreSQL.

**Architecture:** Async SQLAlchemy (asyncpg) for the FastAPI API server. PostgreSQL-specific `INSERT ... ON CONFLICT` for ingestion upserts. FastAPI dependency injection for database sessions. No lifespan table creation — tables are created by the ingestion script.

**Tech Stack:** SQLAlchemy 2.0 (asyncio), asyncpg, PostgreSQL, FastAPI

**Design doc:** `docs/plans/2026-03-08-supabase-to-postgres-design.md`

---

### Task 1: Foundation — Dependencies, Configuration, ORM Model, Database Layer

**Files:**
- Modify: `requirements.txt`
- Modify: `app/config.py`
- Modify: `app/models/schemas.py`
- Modify: `app/db.py`

**Step 1: Update `requirements.txt`**

Replace `supabase>=2.0.0` with SQLAlchemy and asyncpg:

```
fastapi>=0.109.0
uvicorn[standard]>=0.27.0
python-dotenv>=1.0.0
httpx>=0.27.0
pydantic-settings>=2.0.0
sqlalchemy[asyncio]>=2.0.0
asyncpg>=0.29.0
pytest>=8.0.0
pytest-asyncio>=0.23.0
```

**Step 2: Rewrite `app/config.py`**

Replace 3 Supabase settings with a single `database_url`. Add a property to produce the asyncpg-flavored URL so the env var stays as a standard `postgresql://` URL:

```python
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = ""

    @property
    def async_database_url(self) -> str:
        """Convert standard postgresql:// URL to asyncpg URL."""
        return self.database_url.replace(
            "postgresql://", "postgresql+asyncpg://", 1
        )

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

**Step 3: Add ORM model to `app/models/schemas.py`**

Add `Base` and `WarehouseModel` above the existing Pydantic schemas. Add `from_attributes=True` to the Pydantic `Warehouse` model so `model_validate()` works with ORM instances:

```python
import uuid
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date
from uuid import UUID

from sqlalchemy import Column, String, Float, Date, Uuid
from sqlalchemy.orm import DeclarativeBase


# --- SQLAlchemy ORM ---

class Base(DeclarativeBase):
    pass


class WarehouseModel(Base):
    __tablename__ = "warehouses"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
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


# --- Pydantic response schemas ---

class Warehouse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    address: Optional[str] = None
    postal_code: Optional[str] = None
    commune: Optional[str] = None
    department: Optional[str] = None
    surface_m2: Optional[float] = None
    price_eur: Optional[float] = None
    transaction_date: Optional[date] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


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

**Step 4: Rewrite `app/db.py`**

Replace Supabase clients with async SQLAlchemy engine, session factory, and FastAPI dependency:

```python
from collections.abc import AsyncGenerator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings


@lru_cache()
def get_engine() -> AsyncEngine:
    return create_async_engine(get_settings().async_database_url)


@lru_cache()
def get_session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session
```

**Step 5: Install new dependencies**

Run: `pip install -r requirements.txt`

**Step 6: Commit**

```bash
git add requirements.txt app/config.py app/models/schemas.py app/db.py
git commit -m "refactor: replace Supabase SDK with SQLAlchemy async foundation"
```

---

### Task 2: Test Infrastructure

**Files:**
- Modify: `tests/conftest.py`

**Step 1: Rewrite `tests/conftest.py`**

Replace the basic fixture with SQLAlchemy-aware fixtures: a mock async session, a TestClient wired via dependency override, and helper functions for setting up mock return values:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import date

from fastapi.testclient import TestClient

from app.db import get_db_session
from app.main import app
from app.models.schemas import WarehouseModel


def make_warehouse(**overrides) -> WarehouseModel:
    """Create a WarehouseModel instance for testing."""
    defaults = dict(
        id=uuid4(),
        dvf_mutation_id=f"mut-{uuid4().hex[:8]}",
        address="123 Test St",
        postal_code="77000",
        commune="Test City",
        department="77",
        surface_m2=500.0,
        price_eur=100000.0,
        transaction_date=date(2024, 1, 15),
        latitude=48.8566,
        longitude=2.3522,
        property_type="Local industriel. commercial ou assimilé",
    )
    defaults.update(overrides)
    return WarehouseModel(**defaults)


def mock_list_query(mock_session, warehouses, total=None):
    """Configure mock session for list_warehouses endpoint.

    list_warehouses calls session.execute() twice:
    1. COUNT query → scalar() returns total
    2. SELECT query → scalars().all() returns warehouse list
    """
    if total is None:
        total = len(warehouses)

    mock_count = MagicMock()
    mock_count.scalar.return_value = total

    mock_rows = MagicMock()
    mock_rows.scalars.return_value.all.return_value = warehouses

    mock_session.execute = AsyncMock(side_effect=[mock_count, mock_rows])


def mock_stats_query(mock_session, count, avg_price, total_surface):
    """Configure mock session for stats endpoint.

    stats calls session.execute() once → .one() returns (count, avg, sum).
    """
    mock_result = MagicMock()
    mock_result.one.return_value = (count, avg_price, total_surface)
    mock_session.execute = AsyncMock(return_value=mock_result)


@pytest.fixture
def mock_session():
    """Fresh AsyncMock for each test (function-scoped)."""
    return AsyncMock()


@pytest.fixture
def client(mock_session):
    """TestClient with mocked DB session via dependency override."""
    async def override():
        yield mock_session

    app.dependency_overrides[get_db_session] = override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

**Step 2: Commit**

```bash
git add tests/conftest.py
git commit -m "test: rewrite test fixtures for SQLAlchemy session mocking"
```

---

### Task 3: Rewrite API Endpoints and Unit Tests (TDD)

**Files:**
- Modify: `tests/test_api.py`
- Modify: `app/routers/warehouses.py`

**Step 1: Write failing tests**

Replace the entire `tests/test_api.py` with tests that use the new mock helpers:

```python
from tests.conftest import make_warehouse, mock_list_query, mock_stats_query


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestWarehousesEndpoint:
    def test_warehouses_list_returns_200(self, client, mock_session):
        warehouses = [make_warehouse(), make_warehouse()]
        mock_list_query(mock_session, warehouses)

        response = client.get("/api/warehouses")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert len(data["items"]) == 2

    def test_warehouses_pagination(self, client, mock_session):
        warehouses = [make_warehouse() for _ in range(5)]
        mock_list_query(mock_session, warehouses, total=20)

        response = client.get("/api/warehouses?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0
        assert len(data["items"]) == 5

    def test_warehouses_clamp_limit_max(self, client, mock_session):
        mock_list_query(mock_session, [])

        response = client.get("/api/warehouses?limit=999")
        assert response.status_code == 200
        assert response.json()["limit"] == 100

    def test_warehouses_clamp_limit_min(self, client, mock_session):
        mock_list_query(mock_session, [])

        response = client.get("/api/warehouses?limit=-5")
        assert response.status_code == 200
        assert response.json()["limit"] == 1


class TestStatsEndpoint:
    def test_stats_returns_200(self, client, mock_session):
        mock_stats_query(mock_session, count=2, avg_price=125000.0, total_surface=1250.0)

        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "avg_price" in data
        assert "total_surface" in data

    def test_stats_values(self, client, mock_session):
        mock_stats_query(mock_session, count=2, avg_price=125000.0, total_surface=1250.0)

        response = client.get("/api/stats")
        data = response.json()
        assert data["count"] == 2
        assert data["avg_price"] == 125000.0
        assert data["total_surface"] == 1250.0

    def test_stats_empty_db(self, client, mock_session):
        mock_stats_query(mock_session, count=0, avg_price=None, total_surface=None)

        response = client.get("/api/stats")
        data = response.json()
        assert data["count"] == 0
        assert data["avg_price"] == 0.0
        assert data["total_surface"] == 0.0
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_api.py -v`
Expected: FAIL — endpoints still use old Supabase imports

**Step 3: Rewrite `app/routers/warehouses.py`**

Replace Supabase queries with SQLAlchemy ORM. The stats query now computes avg/sum in SQL instead of Python:

```python
from fastapi import APIRouter, Query, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db_session
from app.models.schemas import (
    Warehouse,
    WarehouseListResponse,
    WarehouseModel,
    StatsResponse,
)

router = APIRouter(prefix="/api", tags=["warehouses"])


@router.get("/warehouses", response_model=WarehouseListResponse)
async def list_warehouses(
    limit: int = Query(default=20),
    offset: int = Query(default=0),
    session: AsyncSession = Depends(get_db_session),
):
    limit = max(1, min(100, limit))
    offset = max(0, offset)

    count_result = await session.execute(
        select(func.count()).select_from(WarehouseModel)
    )
    total = count_result.scalar() or 0

    result = await session.execute(
        select(WarehouseModel)
        .order_by(WarehouseModel.transaction_date.desc().nulls_last())
        .limit(limit)
        .offset(offset)
    )
    rows = result.scalars().all()
    items = [Warehouse.model_validate(row) for row in rows]

    return WarehouseListResponse(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    session: AsyncSession = Depends(get_db_session),
):
    result = await session.execute(
        select(
            func.count(WarehouseModel.id),
            func.avg(WarehouseModel.price_eur),
            func.sum(WarehouseModel.surface_m2),
        )
    )
    count, avg_price, total_surface = result.one()

    return StatsResponse(
        count=count or 0,
        avg_price=round(float(avg_price), 2) if avg_price else 0.0,
        total_surface=round(float(total_surface), 2) if total_surface else 0.0,
    )
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_api.py -v`
Expected: All PASS

**Step 5: Commit**

```bash
git add tests/test_api.py app/routers/warehouses.py
git commit -m "refactor: rewrite API endpoints to use SQLAlchemy ORM"
```

---

### Task 4: Rewrite Integration Tests

**Files:**
- Modify: `tests/test_integration.py`

**Step 1: Rewrite `tests/test_integration.py`**

Replace the deeply-nested Supabase mocks with the shared conftest helpers. The tests now use the same `client` and `mock_session` fixtures:

```python
"""Integration tests for the French Real Estate POC API.

Verify the full request/response flow using mocked DB sessions.
"""

from tests.conftest import make_warehouse, mock_list_query, mock_stats_query


class TestIntegrationHealth:
    def test_health_endpoint_returns_healthy_status(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
        assert response.headers["content-type"] == "application/json"


class TestIntegrationWarehouses:
    def test_warehouses_returns_valid_response_structure(self, client, mock_session):
        warehouses = [make_warehouse()]
        mock_list_query(mock_session, warehouses)

        response = client.get("/api/warehouses")
        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["limit"], int)
        assert isinstance(data["offset"], int)

    def test_warehouses_pagination_with_custom_params(self, client, mock_session):
        warehouses = [make_warehouse()]
        mock_list_query(mock_session, warehouses)

        response = client.get("/api/warehouses?limit=10&offset=5")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 5

    def test_warehouses_handles_large_offset_gracefully(self, client, mock_session):
        mock_list_query(mock_session, [], total=0)

        response = client.get("/api/warehouses?offset=10000")
        assert response.status_code == 200
        assert "items" in response.json()

    def test_warehouses_clamps_negative_limit(self, client, mock_session):
        mock_list_query(mock_session, [])

        response = client.get("/api/warehouses?limit=-10")
        assert response.status_code == 200
        assert response.json()["limit"] == 1

    def test_warehouses_clamps_excessive_limit(self, client, mock_session):
        mock_list_query(mock_session, [])

        response = client.get("/api/warehouses?limit=500")
        assert response.status_code == 200
        assert response.json()["limit"] == 100


class TestIntegrationStats:
    def test_stats_returns_valid_response_structure(self, client, mock_session):
        mock_stats_query(
            mock_session, count=1, avg_price=2500000.0, total_surface=15000.0
        )

        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()

        assert "count" in data
        assert "avg_price" in data
        assert "total_surface" in data
        assert isinstance(data["count"], int)
        assert isinstance(data["avg_price"], (int, float))
        assert isinstance(data["total_surface"], (int, float))

    def test_stats_values_are_non_negative(self, client, mock_session):
        mock_stats_query(
            mock_session, count=1, avg_price=2500000.0, total_surface=15000.0
        )

        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 0
        assert data["avg_price"] >= 0
        assert data["total_surface"] >= 0


class TestIntegrationEmptyDatabase:
    def test_warehouses_handles_empty_database(self, client, mock_session):
        mock_list_query(mock_session, [], total=0)

        response = client.get("/api/warehouses")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_stats_handles_empty_database(self, client, mock_session):
        mock_stats_query(mock_session, count=0, avg_price=None, total_surface=None)

        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["avg_price"] == 0.0
        assert data["total_surface"] == 0.0
```

**Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

**Step 3: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: rewrite integration tests for SQLAlchemy"
```

---

### Task 5: Rewrite Ingestion Script

**Files:**
- Modify: `scripts/ingest_dvf.py`

**Step 1: Rewrite `scripts/ingest_dvf.py`**

Replace `insert_to_supabase` with `insert_to_db` using async SQLAlchemy + PostgreSQL upsert. The script creates tables on each run (idempotent via `create_all`). All other functions (`download_dvf`, `parse_row`, `_is_valid_warehouse`, `filter_warehouses`) stay identical:

```python
"""DVF data ingestion script.

Downloads DVF data from data.gouv.fr, filters for large warehouses,
and inserts into PostgreSQL.
"""

import asyncio
import csv
import gzip
import tempfile
import uuid
from pathlib import Path
from urllib.request import urlretrieve

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.config import get_settings
from app.models.schemas import Base, WarehouseModel

DVF_URL_TEMPLATE = (
    "https://files.data.gouv.fr/geo-dvf/latest/csv/2024/departements/{dept}.csv.gz"
)

MAX_WAREHOUSES = 100
MIN_SURFACE_M2 = 10000
WAREHOUSE_TYPE = "Local industriel. commercial ou assimilé"


def download_dvf(department: str) -> Path:
    """Downloads gzipped CSV to temp file, returns path to decompressed CSV."""
    url = DVF_URL_TEMPLATE.format(dept=department)

    temp_gz = tempfile.NamedTemporaryFile(suffix=".csv.gz", delete=False)
    urlretrieve(url, temp_gz.name)

    temp_csv = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
    with gzip.open(temp_gz.name, "rt", encoding="utf-8") as f_in:
        with open(temp_csv.name, "w", encoding="utf-8") as f_out:
            f_out.write(f_in.read())

    Path(temp_gz.name).unlink()
    return Path(temp_csv.name)


def parse_row(row: dict) -> dict | None:
    """Extracts and transforms fields per mapping. Returns None if required fields missing."""
    if not row.get("id_mutation"):
        return None

    numero = row.get("adresse_numero") or ""
    voie = row.get("adresse_nom_voie") or ""
    address = f"{numero} {voie}".strip()

    def parse_float(value: str | None) -> float | None:
        if not value or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def parse_date(value: str | None) -> str | None:
        if not value or value == "":
            return None
        return value

    return {
        "dvf_mutation_id": row.get("id_mutation"),
        "address": address,
        "postal_code": row.get("code_postal") or None,
        "commune": row.get("nom_commune") or None,
        "department": row.get("code_departement") or None,
        "surface_m2": parse_float(row.get("surface_reelle_bati")),
        "price_eur": parse_float(row.get("valeur_fonciere")),
        "transaction_date": parse_date(row.get("date_mutation")),
        "latitude": parse_float(row.get("latitude")),
        "longitude": parse_float(row.get("longitude")),
        "property_type": row.get("type_local") or None,
    }


def _is_valid_warehouse(row: dict) -> bool:
    """Returns True if row should be included."""
    try:
        has_id = bool(row.get("id_mutation"))
        is_warehouse = row.get("type_local") == WAREHOUSE_TYPE
        surface = row.get("surface_reelle_bati")
        has_surface = bool(surface and surface != "")
        has_large_surface = has_surface and float(surface) >= MIN_SURFACE_M2
        price = row.get("valeur_fonciere")
        has_price = bool(price and price != "")
        return has_id and is_warehouse and has_large_surface and has_price
    except (ValueError, TypeError):
        return False


def filter_warehouses(rows: list[dict]) -> list[dict]:
    """Applies filters, returns max 100 qualifying warehouses."""
    warehouses = []
    for row in rows:
        if _is_valid_warehouse(row):
            parsed = parse_row(row)
            if parsed:
                warehouses.append(parsed)
                if len(warehouses) >= MAX_WAREHOUSES:
                    break
    return warehouses


async def _insert_to_db(warehouses: list[dict]) -> int:
    """Async implementation: create tables and insert warehouses."""
    settings = get_settings()
    engine = create_async_engine(settings.async_database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSession(engine) as session:
        for wh in warehouses:
            wh["id"] = uuid.uuid4()
        stmt = (
            pg_insert(WarehouseModel)
            .values(warehouses)
            .on_conflict_do_nothing(index_elements=["dvf_mutation_id"])
        )
        await session.execute(stmt)
        await session.commit()

    await engine.dispose()
    return len(warehouses)


def insert_to_db(warehouses: list[dict]) -> int:
    """Inserts to PostgreSQL. Returns count inserted."""
    if not warehouses:
        return 0
    return asyncio.run(_insert_to_db(warehouses))


def main(department: str = "77") -> None:
    """Orchestrates the pipeline."""
    print(f"Downloading DVF data for department {department}...")
    csv_path = download_dvf(department)

    print("Parsing CSV...")
    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    print(f"Parsed {len(rows)} rows")

    warehouses = filter_warehouses(rows)
    print(f"Filtered to {len(warehouses)} warehouses")

    count = insert_to_db(warehouses)
    print(f"Inserted {count} records")

    csv_path.unlink()


if __name__ == "__main__":
    main()
```

**Step 2: Run ingestion tests to verify they still pass**

Run: `pytest tests/test_ingest.py -v`
Expected: All PASS — these tests only cover `parse_row` and `filter_warehouses` which are unchanged

**Step 3: Commit**

```bash
git add scripts/ingest_dvf.py
git commit -m "refactor: rewrite ingestion script to use SQLAlchemy"
```

---

### Task 6: Update Documentation and Final Verification

**Files:**
- Modify: `.env.example`
- Modify: `CLAUDE.md`

**Step 1: Update `.env.example`**

Replace the 3 Supabase vars with a single `DATABASE_URL`:

```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

**Step 2: Update `CLAUDE.md` environment variables section**

Replace the existing env vars section with:

```markdown
## Environment Variables

See `.env.example`. Required in Coolify:
- `DATABASE_URL` — PostgreSQL connection string (e.g., `postgresql://user:pass@host:5432/dbname`)
```

**Step 3: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests PASS

**Step 4: Commit**

```bash
git add .env.example CLAUDE.md
git commit -m "docs: update env vars for PostgreSQL migration"
```

---

## Post-Implementation: Deployment Steps

After all code tasks are done, the Coolify deployment needs updating:

1. **Set `DATABASE_URL`** in Coolify env vars for app `e4cs4cwowgws4s8sc44ssc8o` — use the connection string from Coolify's managed PostgreSQL
2. **Remove old env vars:** `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_ANON_KEY`
3. **Push to main** — Coolify auto-deploys via webhook
4. **Run ingestion:** `python -m scripts.ingest_dvf` locally (with `DATABASE_URL` pointing to VPS Postgres) to populate the new database
5. **Verify:** `curl https://realestate.kliuiev.com/health` and `curl https://realestate.kliuiev.com/api/warehouses`
