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
