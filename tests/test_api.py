import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient


# Mock the database before importing app
@pytest.fixture(autouse=True)
def mock_db():
    """Mock the Supabase client for all tests."""
    mock_client = MagicMock()

    # Sample warehouse data
    sample_warehouses = [
        {
            "id": str(uuid4()),
            "address": "123 Test St",
            "postal_code": "77000",
            "commune": "Test City",
            "department": "77",
            "surface_m2": 500.0,
            "price_eur": 100000.0,
            "transaction_date": "2024-01-15",
            "latitude": 48.8566,
            "longitude": 2.3522,
        },
        {
            "id": str(uuid4()),
            "address": "456 Mock Ave",
            "postal_code": "77100",
            "commune": "Mock Town",
            "department": "77",
            "surface_m2": 750.0,
            "price_eur": 150000.0,
            "transaction_date": "2024-02-20",
            "latitude": 48.8600,
            "longitude": 2.3600,
        },
    ]

    # Mock for list_warehouses
    mock_result = MagicMock()
    mock_result.data = sample_warehouses
    mock_result.count = len(sample_warehouses)

    # Mock for stats
    mock_stats_count = MagicMock()
    mock_stats_count.count = 2

    mock_stats_data = MagicMock()
    mock_stats_data.data = sample_warehouses

    def mock_table(table_name):
        mock_table_obj = MagicMock()

        def mock_select(*args, **kwargs):
            mock_select_obj = MagicMock()

            def mock_order(*args, **kwargs):
                mock_order_obj = MagicMock()

                def mock_limit(limit):
                    mock_limit_obj = MagicMock()

                    def mock_offset(offset):
                        mock_offset_obj = MagicMock()
                        # Return limited data based on limit
                        limited_data = sample_warehouses[:limit]
                        result = MagicMock()
                        result.data = limited_data
                        result.count = len(sample_warehouses)
                        mock_offset_obj.execute.return_value = result
                        return mock_offset_obj

                    mock_limit_obj.offset = mock_offset
                    return mock_limit_obj

                mock_order_obj.limit = mock_limit
                return mock_order_obj

            mock_select_obj.order = mock_order
            # For stats count query
            mock_select_obj.execute.return_value = (
                mock_stats_count if "id" in args else mock_stats_data
            )
            return mock_select_obj

        mock_table_obj.select = mock_select
        return mock_table_obj

    mock_client.table = mock_table

    with patch("app.db.get_supabase_client", return_value=mock_client):
        with patch("app.db.get_db", return_value=mock_client):
            # Import app after patching
            from app.main import app

            yield app


@pytest.fixture
def client(mock_db):
    """Provides a TestClient for API testing."""
    return TestClient(mock_db)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


class TestWarehousesEndpoint:
    def test_warehouses_list_returns_200(self, client):
        response = client.get("/api/warehouses")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

    def test_warehouses_pagination(self, client):
        response = client.get("/api/warehouses?limit=5&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5
        assert data["offset"] == 0
        assert len(data["items"]) <= 5

    def test_warehouses_clamp_limit_max(self, client):
        response = client.get("/api/warehouses?limit=999")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 100  # Clamped to max

    def test_warehouses_clamp_limit_min(self, client):
        response = client.get("/api/warehouses?limit=-5")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1  # Clamped to min


class TestStatsEndpoint:
    def test_stats_returns_200(self, client):
        response = client.get("/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "count" in data
        assert "avg_price" in data
        assert "total_surface" in data
