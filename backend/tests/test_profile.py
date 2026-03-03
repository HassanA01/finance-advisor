def _register_and_auth(client):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    token = resp.cookies["access_token"]
    client.cookies.set("access_token", token)
    return resp.json()


def test_get_profile(client):
    _register_and_auth(client)
    response = client.get("/profile")
    assert response.status_code == 200
    data = response.json()
    assert data["onboarding_complete"] is False
    assert data["risk_tolerance"] == "medium"
    assert data["fixed_expenses"] == {}


def test_get_profile_unauthenticated(client):
    response = client.get("/profile")
    assert response.status_code == 401


def test_update_profile(client):
    _register_and_auth(client)
    response = client.put(
        "/profile",
        json={
            "net_monthly_income": 4634.42,
            "pay_frequency": "bi-weekly",
            "budget_targets": {"Eating Out": 400, "Groceries": 350},
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["net_monthly_income"] == 4634.42
    assert data["pay_frequency"] == "bi-weekly"
    assert data["budget_targets"]["Eating Out"] == 400


def test_update_profile_partial(client):
    _register_and_auth(client)
    # First update
    client.put("/profile", json={"net_monthly_income": 5000})
    # Second partial update should not clear first
    response = client.put("/profile", json={"pay_frequency": "monthly"})
    data = response.json()
    assert data["pay_frequency"] == "monthly"
    assert data["net_monthly_income"] == 5000


def test_complete_onboarding(client):
    _register_and_auth(client)
    response = client.patch("/profile/onboarding-complete")
    assert response.status_code == 200
    assert response.json()["onboarding_complete"] is True

    # Verify persisted
    get_resp = client.get("/profile")
    assert get_resp.json()["onboarding_complete"] is True
