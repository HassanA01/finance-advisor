import io


def _register_and_auth(client):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    token = resp.cookies["access_token"]
    client.cookies.set("access_token", token)


def _set_budget_targets(client, targets: dict):
    client.put("/profile", json={"budget_targets": targets})


def _upload(client, csv_content, filename="test.csv"):
    return client.post(
        "/transactions/upload",
        files=[("files", (filename, io.BytesIO(csv_content.encode()), "text/csv"))],
    )


JAN_CSV = """Date,Transaction,Debit,Credit
2024-01-15,TIM HORTONS #123,5.50,
2024-01-16,UBER EATS,25.00,
2024-01-17,METRO GROCERY,45.00,
2024-01-19,UBER* TRIP,12.50,
"""

FEB_CSV = """Date,Transaction,Debit,Credit
2024-02-10,TIM HORTONS #456,8.00,
2024-02-12,UBER EATS,40.00,
2024-02-14,METRO GROCERY,60.00,
"""


def test_report_aggregation(client):
    _register_and_auth(client)
    _upload(client, JAN_CSV)
    response = client.get("/reports/2024-01")
    assert response.status_code == 200
    data = response.json()
    assert data["month_key"] == "2024-01"
    assert data["total_spent"] > 0
    spending = data["spending"]
    assert "Eating Out" in spending
    assert "Groceries" in spending


def test_report_vs_target(client):
    _register_and_auth(client)
    _set_budget_targets(client, {"Eating Out": 10.00, "Groceries": 100.00})
    _upload(client, JAN_CSV)
    response = client.get("/reports/2024-01")
    data = response.json()
    vs_target = data["vs_target"]
    # Eating Out: actual 5.50 vs target 10.00 → diff = -4.50
    assert "Eating Out" in vs_target
    assert vs_target["Eating Out"]["target"] == 10.00
    assert vs_target["Eating Out"]["diff"] < 0  # under budget
    # Groceries: actual 45.00 vs target 100.00 → diff = -55.00
    assert "Groceries" in vs_target
    assert vs_target["Groceries"]["diff"] < 0  # under budget


def test_report_vs_prev_month(client):
    _register_and_auth(client)
    _upload(client, JAN_CSV)
    _upload(client, FEB_CSV)
    response = client.get("/reports/2024-02")
    data = response.json()
    vs_prev = data["vs_prev_month"]
    # Eating Out: Feb 8.00 vs Jan 5.50 → increased
    assert "Eating Out" in vs_prev
    assert vs_prev["Eating Out"]["previous"] == 5.50
    assert vs_prev["Eating Out"]["current"] == 8.00
    assert vs_prev["Eating Out"]["diff"] > 0  # spending increased


def test_report_categories_list(client):
    _register_and_auth(client)
    _set_budget_targets(client, {"Eating Out": 20.00})
    _upload(client, JAN_CSV)
    response = client.get("/reports/2024-01")
    data = response.json()
    categories = data["categories"]
    assert len(categories) > 0
    eating = next(c for c in categories if c["category"] == "Eating Out")
    assert eating["amount"] == 5.50
    assert eating["target"] == 20.00
    assert eating["vs_target"] is not None


def test_report_caching(client):
    _register_and_auth(client)
    _upload(client, JAN_CSV)
    # First call generates report
    response1 = client.get("/reports/2024-01")
    data1 = response1.json()
    # Second call returns cached
    response2 = client.get("/reports/2024-01")
    data2 = response2.json()
    assert data1["id"] == data2["id"]


def test_report_regenerate(client):
    _register_and_auth(client)
    _upload(client, JAN_CSV)
    response1 = client.get("/reports/2024-01")
    data1 = response1.json()
    # Regenerate creates new report
    response2 = client.get("/reports/2024-01?regenerate=true")
    data2 = response2.json()
    assert data2["month_key"] == "2024-01"
    # IDs differ because regenerated
    assert data1["id"] != data2["id"]


def test_report_invalid_month_key(client):
    _register_and_auth(client)
    response = client.get("/reports/invalid")
    assert response.status_code == 400


def test_report_empty_month(client):
    _register_and_auth(client)
    response = client.get("/reports/2030-01")
    assert response.status_code == 200
    data = response.json()
    assert data["total_spent"] == 0.0
    assert data["categories"] == []


def test_report_unauthenticated(client):
    response = client.get("/reports/2024-01")
    assert response.status_code == 401
