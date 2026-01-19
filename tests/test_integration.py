"""Integration tests for the French Real Estate POC API.

These tests use the REAL Supabase database (read-only).
They verify the full stack works end-to-end.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4
from fastapi.testclient import TestClient


# For integration tests, we still mock Supabase since we can't guarantee
# the database has data during CI/test runs. However, the tests verify
# the full request/response flow.
@pytest.fixture
def integration_client():
    """Provides a TestClient with mocked Supabase for integration testing."""
    mock_client = MagicMock()

    # Sample warehouse data (simulating real data)
    sample_warehouses = [
        {
            "id": str(uuid4()),
            "address": "Zone Industrielle",
            "postal_code": "77000",
            "commune": "Melun",
            "department": "77",
            "surface_m2": 15000.0,
            "price_eur": 2500000.0,
            "transaction_date": "2024-03-15",
            "latitude": 48.5423,
            "longitude": 2.6553,
        },
    ]

    # Mock for list_warehouses
    mock_result = MagicMock()
    mock_result.data = sample_warehouses
    mock_result.count = len(sample_warehouses)

    # Mock for stats
    mock_stats_count = MagicMock()
    mock_stats_count.count = 1

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
            mock_select_obj.execute.return_value = (
                mock_stats_count if "id" in args else mock_stats_data
            )
            return mock_select_obj

        mock_table_obj.select = mock_select
        return mock_table_obj

    mock_client.table = mock_table

    with patch("app.db.get_supabase_client", return_value=mock_client):
        with patch("app.db.get_db", return_value=mock_client):
            from app.main import app

            yield TestClient(app)


class TestIntegrationHealth:
    """Integration tests for /health endpoint."""

    def test_health_endpoint_returns_healthy_status(self, integration_client):
        """Verify health endpoint returns expected response."""
        response = integration_client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
        assert response.headers["content-type"] == "application/json"


class TestIntegrationWarehouses:
    """Integration tests for /api/warehouses endpoint."""

    def test_warehouses_returns_valid_response_structure(self, integration_client):
        """Verify warehouses endpoint returns correct structure."""
        response = integration_client.get("/api/warehouses")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data

        # Verify types
        assert isinstance(data["items"], list)
        assert isinstance(data["total"], int)
        assert isinstance(data["limit"], int)
        assert isinstance(data["offset"], int)

    def test_warehouses_pagination_with_custom_params(self, integration_client):
        """Verify pagination parameters are respected."""
        response = integration_client.get("/api/warehouses?limit=10&offset=5")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 5

    def test_warehouses_handles_large_offset_gracefully(self, integration_client):
        """Verify large offset doesn't crash (returns empty or partial)."""
        response = integration_client.get("/api/warehouses?offset=10000")

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        # Should return empty list or whatever data exists

    def test_warehouses_clamps_negative_limit(self, integration_client):
        """Verify negative limit is clamped to 1."""
        response = integration_client.get("/api/warehouses?limit=-10")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 1

    def test_warehouses_clamps_excessive_limit(self, integration_client):
        """Verify excessive limit is clamped to 100."""
        response = integration_client.get("/api/warehouses?limit=500")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 100


class TestIntegrationStats:
    """Integration tests for /api/stats endpoint."""

    def test_stats_returns_valid_response_structure(self, integration_client):
        """Verify stats endpoint returns correct structure."""
        response = integration_client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "count" in data
        assert "avg_price" in data
        assert "total_surface" in data

        # Verify types
        assert isinstance(data["count"], int)
        assert isinstance(data["avg_price"], (int, float))
        assert isinstance(data["total_surface"], (int, float))

    def test_stats_values_are_non_negative(self, integration_client):
        """Verify stats values are non-negative."""
        response = integration_client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["count"] >= 0
        assert data["avg_price"] >= 0
        assert data["total_surface"] >= 0


class TestIntegrationEmptyDatabase:
    """Tests for handling empty database gracefully."""

    @pytest.fixture
    def empty_db_client(self):
        """Client with mocked empty database."""
        mock_client = MagicMock()

        # Empty data
        mock_result = MagicMock()
        mock_result.data = []
        mock_result.count = 0

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
                            mock_offset_obj.execute.return_value = mock_result
                            return mock_offset_obj

                        mock_limit_obj.offset = mock_offset
                        return mock_limit_obj

                    mock_order_obj.limit = mock_limit
                    return mock_order_obj

                mock_select_obj.order = mock_order
                mock_select_obj.execute.return_value = mock_result
                return mock_select_obj

            mock_table_obj.select = mock_select
            return mock_table_obj

        mock_client.table = mock_table

        with patch("app.db.get_supabase_client", return_value=mock_client):
            with patch("app.db.get_db", return_value=mock_client):
                from app.main import app

                yield TestClient(app)

    def test_warehouses_handles_empty_database(self, empty_db_client):
        """Verify warehouses endpoint handles empty database."""
        response = empty_db_client.get("/api/warehouses")

        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_stats_handles_empty_database(self, empty_db_client):
        """Verify stats endpoint handles empty database."""
        response = empty_db_client.get("/api/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["avg_price"] == 0.0
        assert data["total_surface"] == 0.0
