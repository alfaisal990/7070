def test_create_task_unauthenticated(client):
    response = client.post(
        "/api/tasks",
        json={"title": "Test Task", "description": "Needs to run"}
    )
    assert response.status_code == 401

def test_tasks_crud_lifecycle(client):
    client.post(
        "/api/auth/register",
        json={"email": "crud@example.com", "password": "password123"}
    )
    login_response = client.post(
        "/api/auth/login",
        data={"username": "crud@example.com", "password": "password123"}
    )
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    create_response = client.post(
        "/api/tasks",
        json={"title": "My First Task", "description": "Doing CRUD lifecycle testing"},
        headers=headers
    )
    assert create_response.status_code == 201
    task_data = create_response.json()
    assert task_data["title"] == "My First Task"
    assert task_data["is_completed"] is False
    task_id = task_data["id"]

    list_response = client.get("/api/tasks", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()) == 1
    assert list_response.json()[0]["id"] == task_id

    detail_response = client.get(f"/api/tasks/{task_id}", headers=headers)
    assert detail_response.status_code == 200
    assert detail_response.json()["title"] == "My First Task"

    update_response = client.put(
        f"/api/tasks/{task_id}",
        json={"title": "My Updated Task", "is_completed": True},
        headers=headers
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "My Updated Task"
    assert update_response.json()["is_completed"] is True

    delete_response = client.delete(f"/api/tasks/{task_id}", headers=headers)
    assert delete_response.status_code == 204

    get_again = client.get(f"/api/tasks/{task_id}", headers=headers)
    assert get_again.status_code == 404
