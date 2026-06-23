from fastapi.testclient import TestClient
from ai_project.api.main import app, chat_limiter

def test_rate_limiting():
    # Save original limit and configure a low limit for the test
    orig_limit = chat_limiter.limit
    chat_limiter.limit = 3
    chat_limiter.requests.clear()
    
    with TestClient(app) as client:
        # First 3 requests should succeed
        for _ in range(3):
            response = client.get("/api/chat/stream?prompt=Hello")
            assert response.status_code == 200
            
        # The 4th request must exceed the limit and return HTTP 429
        response = client.get("/api/chat/stream?prompt=Hello")
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
        
    # Restore original limit
    chat_limiter.limit = orig_limit
