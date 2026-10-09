"""
Comprehensive tests for the Milo FastAPI layer.
Tests chat endpoint (validation, error formatting, mock execution),
health endpoint, dataset metadata endpoint, and absence of secrets in responses.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import CSV_PATH
from app.data_loader import load_orders
from app.agent import MiloProviderError, MiloSafetyError


@pytest.fixture(scope="module")
def client():
    """Test client with loaded dataset."""
    load_orders(CSV_PATH)
    with TestClient(app) as test_client:
        yield test_client


# ──────────────────────────── Health & Dataset Endpoints ────────────────────────────


def test_health_endpoint_healthy(client: TestClient):
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["data_loaded"] is True
    assert isinstance(data["ai_configured"], bool)

    # Security check: no secrets or paths leaked
    raw_text = response.text.lower()
    assert "orders.csv" not in raw_text
    assert "c:\\" not in raw_text
    assert "api_key" not in raw_text


def test_health_endpoint_data_not_ready():
    with TestClient(app) as test_client:
        app.state.dataset_loaded = False
        response = test_client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "data-not-ready"
        assert data["data_loaded"] is False
        # Reset state back to loaded
        app.state.dataset_loaded = True


def test_dataset_endpoint_success(client: TestClient):
    response = client.get("/api/dataset")
    assert response.status_code == 200
    data = response.json()
    assert data["record_count"] == 60
    assert data["start_date"] == "2026-06-01"
    assert data["end_date"] == "2026-09-28"

    # Security check: no internal path disclosure
    assert "path" not in data
    assert "csv" not in response.text.lower()


def test_dataset_endpoint_not_ready():
    with TestClient(app) as test_client:
        app.state.dataset_loaded = False
        response = test_client.get("/api/dataset")
        assert response.status_code == 503
        app.state.dataset_loaded = True


# ──────────────────────────── Chat Endpoint Tests ────────────────────────────


def test_chat_valid_request(client: TestClient, monkeypatch):
    """Valid request with mocked agent returns {reply: str, error: null}."""
    async def mock_agent_chat(message: str):
        return {
            "reply": "Order ORD-1025 is Delivered.",
            "tool_used": "lookup_order",
        }

    monkeypatch.setattr("app.main.agent_chat", mock_agent_chat)

    response = client.post("/api/chat", json={"message": "Where is order ORD-1025?"})
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Order ORD-1025 is Delivered."
    assert data["error"] is None


def test_chat_empty_and_whitespace_rejected(client: TestClient):
    """Empty or whitespace-only messages produce 422 with {reply: null, error: str}."""
    res_empty = client.post("/api/chat", json={"message": ""})
    assert res_empty.status_code == 422
    data_empty = res_empty.json()
    assert data_empty["reply"] is None
    assert data_empty["error"] is not None

    res_spaces = client.post("/api/chat", json={"message": "     "})
    assert res_spaces.status_code == 422
    data_spaces = res_spaces.json()
    assert data_spaces["reply"] is None
    assert data_spaces["error"] is not None


def test_chat_exceeds_max_length(client: TestClient):
    """Message exceeding 2000 chars produces 422."""
    long_msg = "a" * 2001
    response = client.post("/api/chat", json={"message": long_msg})
    assert response.status_code == 422
    data = response.json()
    assert data["reply"] is None
    assert data["error"] is not None


def test_chat_wrong_types(client: TestClient):
    """Invalid payload types produce 422."""
    res_num = client.post("/api/chat", json={"message": 12345})
    assert res_num.status_code == 422

    res_list = client.post("/api/chat", json={"message": ["hello"]})
    assert res_list.status_code == 422


def test_chat_malformed_json(client: TestClient):
    """Malformed JSON payload produces 400 or 422 structured error."""
    response = client.post(
        "/api/chat",
        content="not a json string at all",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code in [400, 422]
    data = response.json()
    assert data["reply"] is None
    assert data["error"] is not None


def test_chat_provider_failure_handled(client: TestClient, monkeypatch):
    """Provider failure produces 503 with friendly generic message in {reply: null, error}."""
    async def mock_fail(message: str):
        raise MiloProviderError("Quota exceeded on model")

    monkeypatch.setattr("app.main.agent_chat", mock_fail)

    response = client.post("/api/chat", json={"message": "Any orders?"})
    assert response.status_code == 503
    data = response.json()
    assert data["reply"] is None
    assert "temporarily unavailable" in data["error"].lower()


def test_chat_safety_block_handled(client: TestClient, monkeypatch):
    """Safety policy block produces 400 with friendly message."""
    async def mock_safety(message: str):
        raise MiloSafetyError("Safety policy violation")

    monkeypatch.setattr("app.main.agent_chat", mock_safety)

    response = client.post("/api/chat", json={"message": "Dangerous prompt"})
    assert response.status_code == 400
    data = response.json()
    assert data["reply"] is None
    assert "safety policies" in data["error"].lower()


def test_chat_unexpected_exception_hides_stack_trace(client: TestClient, monkeypatch):
    """Unexpected exception produces generic 500 with no trace leaked in response body."""
    secret_text = "SECRET_STACK_TRACE_LEAK_DATABASE_PASSWORD"

    async def mock_crash(message: str):
        raise RuntimeError(f"Internal crash with {secret_text}")

    monkeypatch.setattr("app.main.agent_chat", mock_crash)

    response = client.post("/api/chat", json={"message": "Trigger crash"})
    assert response.status_code == 500
    data = response.json()
    assert data["reply"] is None
    assert secret_text not in response.text
    assert "error" in data
