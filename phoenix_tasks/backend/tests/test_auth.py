def test_register_and_login_flow(client):
    reg_response = client.post(
        "/api/auth/register",
        json={"email": "member@example.com", "password": "password123", "role": "member"}
    )
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert reg_data["email"] == "member@example.com"
    assert reg_data["role"] == "member"

    login_response = client.post(
        "/api/auth/login",
        data={"username": "member@example.com", "password": "password123"}
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == "member@example.com"
