"""Tests for the API endpoints (no Gemini calls — just health + validation)."""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["orders_loaded"] == 60
    assert "model" in data


def test_chat_endpoint_requires_message(client):
    response = client.post("/api/chat", json={})
    assert response.status_code == 422  # Validation error


def test_chat_endpoint_rejects_empty_message(client):
    response = client.post("/api/chat", json={"message": ""})
    assert response.status_code == 422
