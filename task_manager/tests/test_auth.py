def test_register_user(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "securepassword"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert data["is_active"] is True

def test_register_duplicate_user(client):
    response1 = client.post(
        "/api/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"}
    )
    assert response1.status_code == 201
    
    response2 = client.post(
        "/api/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"}
    )
    assert response2.status_code == 400
    assert response2.json()["detail"] == "Email already registered"

def test_login_success(client):
    client.post(
        "/api/auth/register",
        json={"email": "login@example.com", "password": "correct_password"}
    )
    
    response = client.post(
        "/api/auth/login",
        data={"username": "login@example.com", "password": "correct_password"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_incorrect_credentials(client):
    client.post(
        "/api/auth/register",
        json={"email": "wrong@example.com", "password": "correct_password"}
    )
    
    response = client.post(
        "/api/auth/login",
        data={"username": "wrong@example.com", "password": "bad_password"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"
