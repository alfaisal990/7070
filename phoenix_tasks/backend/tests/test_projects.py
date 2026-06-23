def test_project_permissions_and_crud(client):
    client.post("/api/auth/register", json={"email": "admin@example.com", "password": "password123", "role": "admin"})
    client.post("/api/auth/register", json={"email": "member@example.com", "password": "password123", "role": "member"})

    adm_login = client.post("/api/auth/login", data={"username": "admin@example.com", "password": "password123"})
    adm_token = adm_login.json()["access_token"]
    adm_headers = {"Authorization": f"Bearer {adm_token}"}

    mem_login = client.post("/api/auth/login", data={"username": "member@example.com", "password": "password123"})
    mem_token = mem_login.json()["access_token"]
    mem_headers = {"Authorization": f"Bearer {mem_token}"}

    response = client.post("/api/projects", json={"name": "Forbidden Project"}, headers=mem_headers)
    assert response.status_code == 403

    response = client.post("/api/projects", json={"name": "SaaS Platform", "description": "Building Phoenix SaaS"}, headers=adm_headers)
    assert response.status_code == 201
    project_id = response.json()["id"]

    list_response = client.get("/api/projects", headers=mem_headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1

    response = client.put(f"/api/projects/{project_id}", json={"name": "Hacked Name"}, headers=mem_headers)
    assert response.status_code == 403

    response = client.put(f"/api/projects/{project_id}", json={"name": "SaaS Platform v2"}, headers=adm_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "SaaS Platform v2"

    response = client.delete(f"/api/projects/{project_id}", headers=adm_headers)
    assert response.status_code == 204
