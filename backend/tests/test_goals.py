def _register_and_auth(client):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    token = resp.cookies["access_token"]
    client.cookies.set("access_token", token)


def test_create_goal(client):
    _register_and_auth(client)
    response = client.post(
        "/goals",
        json={"name": "Emergency Fund", "target_amount": 5000},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Emergency Fund"
    assert data["target_amount"] == 5000
    assert data["current_amount"] == 0
    assert data["status"] == "active"


def test_create_goal_with_deadline(client):
    _register_and_auth(client)
    response = client.post(
        "/goals",
        json={
            "name": "Vacation Fund",
            "target_amount": 3000,
            "deadline": "2025-06-01T00:00:00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["deadline"] is not None


def test_list_goals(client):
    _register_and_auth(client)
    client.post("/goals", json={"name": "Goal A", "target_amount": 1000})
    client.post("/goals", json={"name": "Goal B", "target_amount": 2000})
    response = client.get("/goals")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_update_goal(client):
    _register_and_auth(client)
    create_resp = client.post(
        "/goals",
        json={"name": "Save Up", "target_amount": 1000},
    )
    goal_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/goals/{goal_id}",
        json={"current_amount": 250, "name": "Save More"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["current_amount"] == 250
    assert data["name"] == "Save More"


def test_update_goal_status(client):
    _register_and_auth(client)
    create_resp = client.post(
        "/goals",
        json={"name": "Goal", "target_amount": 500},
    )
    goal_id = create_resp.json()["id"]

    update_resp = client.put(
        f"/goals/{goal_id}",
        json={"status": "completed"},
    )
    assert update_resp.json()["status"] == "completed"


def test_delete_goal(client):
    _register_and_auth(client)
    create_resp = client.post(
        "/goals",
        json={"name": "Delete Me", "target_amount": 100},
    )
    goal_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/goals/{goal_id}")
    assert delete_resp.status_code == 204

    # Verify it's gone
    list_resp = client.get("/goals")
    assert len(list_resp.json()) == 0


def test_update_nonexistent_goal(client):
    _register_and_auth(client)
    response = client.put(
        "/goals/nonexistent",
        json={"name": "Updated"},
    )
    assert response.status_code == 404


def test_delete_nonexistent_goal(client):
    _register_and_auth(client)
    response = client.delete("/goals/nonexistent")
    assert response.status_code == 404


def test_goals_unauthenticated(client):
    response = client.get("/goals")
    assert response.status_code == 401
