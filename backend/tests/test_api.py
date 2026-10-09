"""Tests for API endpoints (health, data-not-ready, chat validation)."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.data_loader import DatasetError, load_orders
from app.config import CSV_PATH


@pytest.fixture
def client():
    load_orders(CSV_PATH)
    return TestClient(app)


def test_health_endpoint_healthy(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["orders_loaded"] == 60
    assert "model" in data


def test_health_endpoint_data_not_ready(monkeypatch):
    """When dataset fails to load, healthcheck reports data-not-ready."""
    def mock_get_orders():
        raise DatasetError("Dataset not ready")

    monkeypatch.setattr("app.main.get_orders", mock_get_orders)
    test_client = TestClient(app)
    response = test_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "data-not-ready"
    assert data["orders_loaded"] == 0


def test_chat_endpoint_requires_message(client):
    response = client.post("/api/chat", json={})
    assert response.status_code == 422


def test_chat_endpoint_rejects_empty_message(client):
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422
