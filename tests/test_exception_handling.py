from fastapi.testclient import TestClient
from unittest.mock import patch
from ai_project.api.main import app
from ai_project.api.auth import create_access_token, Roles

def test_exception_sanitization():
    client = TestClient(app)
    
    # Mock agent.run_loop to raise an internal exception containing sensitive info
    with patch("ai_project.api.main.agent") as mock_agent:
        if mock_agent is not None:
            mock_agent.run_loop.side_effect = ValueError("Database connection lost! Secret key is xyz123.")
            
        payload = {"prompt": "test exception", "temperature": 0.2, "max_tokens": 128}
        token = create_access_token("u1", "testuser", Roles.USER)
        response = client.post("/api/chat", json=payload, headers={"Authorization": f"Bearer {token}"})
        
        # Verify status is 500 Internal Server Error
        assert response.status_code == 500
        
        # Verify response detail is sanitized and contains no trace details
        data = response.json()
        assert "Internal server error" in data["detail"]
        assert "Traceback ID" in data["detail"]
        assert "xyz123" not in data["detail"]
        assert "ValueError" not in data["detail"]
