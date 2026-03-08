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
