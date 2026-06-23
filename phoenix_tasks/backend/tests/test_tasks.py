def test_tasks_and_dashboard_flow(client):
    client.post("/api/auth/register", json={"email": "admin@example.com", "password": "password123", "role": "admin"})
    adm_login = client.post("/api/auth/login", data={"username": "admin@example.com", "password": "password123"})
    token = adm_login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = client.post("/api/projects", json={"name": "Tasks Project"}, headers=headers)
    project_id = proj_res.json()["id"]

    task_res = client.post(
        f"/api/projects/{project_id}/tasks",
        json={"title": "Fix Frontend", "description": "Needs styling", "priority": "high"},
        headers=headers
    )
    assert task_res.status_code == 201
    task_id = task_res.json()["id"]

    get_res = client.get(f"/api/tasks/{task_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Fix Frontend"

    comment_res = client.post(
        f"/api/tasks/{task_id}/comments",
        json={"content": "I am working on this"},
        headers=headers
    )
    assert comment_res.status_code == 201
    assert comment_res.json()["content"] == "I am working on this"

    comments_list = client.get(f"/api/tasks/{task_id}/comments", headers=headers)
    assert comments_list.status_code == 200
    assert len(comments_list.json()) == 1

    stats_res = client.get("/api/dashboard/stats", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_projects"] == 1
    assert stats["total_tasks"] == 1
    assert stats["todo_tasks"] == 1
    assert stats["high_priority_tasks"] == 1

    act_res = client.get("/api/activities", headers=headers)
    assert act_res.status_code == 200
    assert len(act_res.json()) > 0
