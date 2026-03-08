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
