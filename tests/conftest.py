import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Provides a TestClient for API testing."""
    return TestClient(app)
