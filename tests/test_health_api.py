"""
Tests for the Phoenix AI Health API endpoint and input validation.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from ai_project.api.auth import create_access_token, Roles


def make_test_client():
    """Creates a test client with mocked model components."""
    import ai_project.api.main as api_module

    # Mock minimal dependencies — need real-ish parameter objects
    mock_param = MagicMock()
    mock_param.numel.return_value = 54000000
    mock_param.device = "cpu"
    mock_param.requires_grad = True

    mock_model = MagicMock()
    # parameters() is called both for sum() and next(), so return a fresh iterator each time
    mock_model.parameters = MagicMock(side_effect=lambda: iter([mock_param]))
    mock_model.args = MagicMock()
    mock_model.args.max_seq_len = 1024
    mock_model.is_trained = False

    api_module.model = mock_model
    api_module.tokenizer = MagicMock()
    api_module.tokenizer.get_vocab_size.return_value = 32000
    api_module.memory_store = MagicMock()
    api_module.memory_store.memories = []
    api_module.memory_store.search_memories.return_value = []
    api_module.sandbox = MagicMock()
    api_module.engine = MagicMock()
    api_module.agent = MagicMock()
    api_module.debugger_agent = MagicMock()
    api_module.refactor_agent = MagicMock()
    api_module.evaluator = MagicMock()
    api_module.STARTUP_TIME = 1000000.0

    return TestClient(api_module.app)


def test_health_endpoint_returns_correct_structure():
    """Tests that /api/health returns the expected JSON structure."""
    client = make_test_client()
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["version"] == "2.0.0"
    assert "uptime_seconds" in data
    assert "model" in data
    assert "memory" in data
    assert "tokenizer" in data


def test_health_endpoint_model_info():
    """Tests that health endpoint includes model details."""
    client = make_test_client()
    res = client.get("/api/health")
    data = res.json()
    assert data["model"]["name"] == "Phoenix-54M"
    assert "parameters" in data["model"]
    assert "is_trained" in data["model"]


def test_memory_search_endpoint():
    """Tests that /api/memory/search accepts POST and returns results."""
    client = make_test_client()
    token = create_access_token("u1", "testuser", Roles.USER)
    res = client.post("/api/memory/search", json={"query": "test query", "top_n": 3}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "results" in data


def test_memory_clear_endpoint():
    """Tests that /api/memory/clear clears all memories."""
    client = make_test_client()
    token = create_access_token("u1", "admin", Roles.ADMIN)
    res = client.delete("/api/memory/clear", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"


def test_chat_prompt_validation():
    """Tests that oversized prompts are rejected by Pydantic validation."""
    client = make_test_client()
    token = create_access_token("u1", "testuser", Roles.USER)
    oversized_prompt = "x" * 10001
    res = client.post("/api/chat", json={"prompt": oversized_prompt}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 422  # Pydantic validation error


def test_sandbox_timeout_validation():
    """Tests that excessive timeout values are rejected."""
    client = make_test_client()
    token = create_access_token("u1", "dev", Roles.DEVELOPER)
    res = client.post("/api/sandbox/run", json={"code": "print(1)", "timeout": 999.0}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 422  # Pydantic validation error


def test_sandbox_code_size_validation():
    """Tests that oversized code submissions are rejected."""
    client = make_test_client()
    token = create_access_token("u1", "dev", Roles.DEVELOPER)
    oversized_code = "x = 1\n" * 20000  # ~120KB
    res = client.post("/api/sandbox/run", json={"code": oversized_code}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 422  # Pydantic max_length validation


def test_liveness_endpoint():
    """Tests the /api/health/liveness endpoint."""
    client = make_test_client()
    res = client.get("/api/health/liveness")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert "uptime_seconds" in data


def test_readiness_endpoint():
    """Tests the /api/health/readiness endpoint."""
    client = make_test_client()
    res = client.get("/api/health/readiness")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ready"
    assert data["components"]["model"] is True
    assert data["components"]["tokenizer"] is True
    assert data["components"]["memory_store"] is True
    assert data["components"]["engine"] is True

