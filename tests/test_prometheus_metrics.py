import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
import ai_project.api.main as api_module
from ai_project.api.auth import create_access_token, Roles

def test_prometheus_metrics_endpoint():
    from ai_project.api.monitoring import PhoenixMonitor
    
    mock_monitor = PhoenixMonitor()
    mock_monitor.total_requests = 10
    mock_monitor.successful_requests = 8
    mock_monitor.failed_requests = 2
    mock_monitor.active_requests = 1
    mock_monitor.accumulated_latency = 5.5
    mock_monitor.total_tokens_generated = 1500
    mock_monitor.total_prefill_time = 0.5
    mock_monitor.total_decode_time = 3.2
    mock_monitor.generation_sessions = 5
    
    old_monitor = api_module.monitor
    api_module.monitor = mock_monitor
    
    try:
        client = TestClient(api_module.app)
        res = client.get("/metrics")
        assert res.status_code == 200
        assert "text/plain" in res.headers["content-type"]
        
        content = res.text
        assert "# HELP phoenix_api_requests_total" in content
        assert "# TYPE phoenix_api_requests_total counter" in content
        assert 'phoenix_api_requests_total{status="all"} 10' in content
        assert 'phoenix_api_requests_total{status="success"} 8' in content
        assert 'phoenix_api_requests_total{status="failed"} 2' in content
        
        assert "# HELP phoenix_api_active_requests" in content
        assert "phoenix_api_active_requests 1" in content
        
        assert "# HELP phoenix_api_latency_seconds_total" in content
        assert "phoenix_api_latency_seconds_total 5.5" in content
        
        assert "# HELP phoenix_llm_tokens_generated_total" in content
        assert "phoenix_llm_tokens_generated_total 1500" in content
        
        assert "# HELP phoenix_llm_prefill_seconds_total" in content
        assert "phoenix_llm_prefill_seconds_total 0.5" in content
        
        assert "# HELP phoenix_llm_decode_seconds_total" in content
        assert "phoenix_llm_decode_seconds_total 3.2" in content
        
        assert "# HELP phoenix_llm_generation_sessions_total" in content
        assert "phoenix_llm_generation_sessions_total 5" in content
    finally:
        api_module.monitor = old_monitor

def test_api_memory_search_graph_rag_route():
    from ai_project.api.main import MemorySearchRequest
    req = MemorySearchRequest(query="test query", top_n=2, mode="graph_rag")
    assert req.mode == "graph_rag"
    
    mock_store = MagicMock()
    mock_store.search_graph_rag.return_value = [{"text": "graph match", "similarity": 0.9, "metadata": {}}]
    
    old_store = api_module.memory_store
    api_module.memory_store = mock_store
    
    try:
        client = TestClient(api_module.app)
        token = create_access_token("u1", "testuser", Roles.USER)
        res = client.post("/api/memory/search", json={"query": "test query", "top_n": 2, "mode": "graph_rag"}, headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200
        data = res.json()
        assert "results" in data
        assert data["results"][0]["text"] == "graph match"
        mock_store.search_graph_rag.assert_called_once_with("test query", top_n=2)
    finally:
        api_module.memory_store = old_store
