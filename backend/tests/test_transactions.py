import io


def _register_and_auth(client):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    token = resp.cookies["access_token"]
    client.cookies.set("access_token", token)


DEBIT_CSV = """Date,Transaction,Debit,Credit
2024-01-15,TIM HORTONS #123,5.50,
2024-01-16,UBER EATS,25.00,
2024-01-17,METRO GROCERY,45.00,
2024-01-18,INTERNET TRANSFER,,500.00
2024-01-19,UBER* TRIP,12.50,
"""

CREDIT_CSV = """Date,Transaction,Payment,Credit
2024-02-01,AMAZON.CA,,89.99
2024-02-02,PAYMENT THANK YOU,500.00,
2024-02-03,STARBUCKS,,6.50
"""


def _upload(client, csv_content, filename="test.csv"):
    return client.post(
        "/transactions/upload",
        files=[("files", (filename, io.BytesIO(csv_content.encode()), "text/csv"))],
    )


def test_upload_debit_csv(client):
    _register_and_auth(client)
    response = _upload(client, DEBIT_CSV)
    assert response.status_code == 201
    data = response.json()
    # 4 transactions: TIM HORTONS, UBER EATS, METRO, UBER TRIP
    # INTERNET TRANSFER is credit (money in) so skipped
    assert data["uploaded"] == 4
    assert data["duplicates_skipped"] == 0
    assert "2024-01" in data["months_affected"]


def test_upload_credit_csv(client):
    _register_and_auth(client)
    response = _upload(client, CREDIT_CSV)
    assert response.status_code == 201
    data = response.json()
    # AMAZON + STARBUCKS (PAYMENT THANK YOU skipped as credit card payment)
    assert data["uploaded"] == 2
    assert "2024-02" in data["months_affected"]


def test_upload_deduplication(client):
    _register_and_auth(client)
    _upload(client, DEBIT_CSV)
    response = _upload(client, DEBIT_CSV)
    data = response.json()
    assert data["uploaded"] == 0
    assert data["duplicates_skipped"] == 4


def test_categorization(client):
    _register_and_auth(client)
    _upload(client, DEBIT_CSV)
    response = client.get("/transactions")
    txns = response.json()
    categories = {t["description"]: t["category"] for t in txns}
    assert categories["TIM HORTONS #123"] == "Eating Out"
    assert categories["UBER EATS"] == "Uber Eats"
    assert categories["METRO GROCERY"] == "Groceries"
    assert categories["UBER* TRIP"] == "Transportation - Rideshare"


def test_list_transactions_filter_month(client):
    _register_and_auth(client)
    _upload(client, DEBIT_CSV)
    _upload(client, CREDIT_CSV)
    response = client.get("/transactions?month=2024-01")
    assert len(response.json()) == 4


def test_list_transactions_filter_category(client):
    _register_and_auth(client)
    _upload(client, DEBIT_CSV)
    response = client.get("/transactions?category=Eating Out")
    assert all(t["category"] == "Eating Out" for t in response.json())


def test_list_transactions_search(client):
    _register_and_auth(client)
    _upload(client, DEBIT_CSV)
    response = client.get("/transactions?search=uber")
    txns = response.json()
    assert len(txns) == 2  # UBER EATS + UBER* TRIP


def test_list_months(client):
    _register_and_auth(client)
    _upload(client, DEBIT_CSV)
    _upload(client, CREDIT_CSV)
    response = client.get("/transactions/months")
    months = response.json()
    assert "2024-01" in months
    assert "2024-02" in months


def test_list_categories(client):
    _register_and_auth(client)
    _upload(client, DEBIT_CSV)
    response = client.get("/transactions/categories")
    categories = response.json()
    assert "Eating Out" in categories
    assert "Groceries" in categories


def test_upload_unauthenticated(client):
    response = _upload(client, DEBIT_CSV)
    assert response.status_code == 401


# --- Headerless CSV tests (real CIBC format) ---

HEADERLESS_DEBIT_CSV = """2024-03-01,TIM HORTONS #456,4.75,
2024-03-02,UBER EATS,18.50,
2024-03-03,LOBLAWS,62.30,
2024-03-04,PAYROLL DEPOSIT,,2317.21
"""

HEADERLESS_CREDIT_CARD_CSV = """2024-04-10,AMAZON.CA,45.99,,1234
2024-04-11,NETFLIX,16.99,,1234
2024-04-12,STARBUCKS,7.25,,1234
"""

HEADERLESS_MIXED_CSV = """2024-05-01,SHOPPERS DRUG MART,12.50,
2024-05-02,INTERNET TRANSFER,,500.00
2024-05-03,METRO GROCERY,33.75,
"""


def test_upload_headerless_debit_csv(client):
    _register_and_auth(client)
    response = _upload(client, HEADERLESS_DEBIT_CSV, "debit_march.csv")
    assert response.status_code == 201
    data = response.json()
    # 3 debit transactions; PAYROLL DEPOSIT is credit (money in) → skipped
    assert data["uploaded"] == 3
    assert "2024-03" in data["months_affected"]


def test_upload_headerless_credit_card_csv(client):
    _register_and_auth(client)
    response = _upload(client, HEADERLESS_CREDIT_CARD_CSV, "visa_april.csv")
    assert response.status_code == 201
    data = response.json()
    assert data["uploaded"] == 3
    assert "2024-04" in data["months_affected"]

    # Verify source is credit_card
    txns = client.get("/transactions?month=2024-04").json()
    assert all(t["source"] == "credit_card" for t in txns)


def test_upload_headerless_skips_credit_rows(client):
    _register_and_auth(client)
    response = _upload(client, HEADERLESS_MIXED_CSV, "mixed.csv")
    assert response.status_code == 201
    data = response.json()
    # SHOPPERS + METRO = 2 debits; INTERNET TRANSFER is credit → skipped
    assert data["uploaded"] == 2


def test_upload_headerless_family_support(client, db):
    _register_and_auth(client)

    # Set up family support recipients on the user profile
    from app.models.user import UserProfile

    profile = db.query(UserProfile).first()
    profile.family_support_recipients = ["Ammi"]
    db.commit()

    csv = "2024-06-01,INTERAC E-TRANSFER TO AMMI,400.00,\n"
    response = _upload(client, csv, "etransfer.csv")
    assert response.status_code == 201
    data = response.json()
    assert data["uploaded"] == 1

    txns = client.get("/transactions?month=2024-06").json()
    assert txns[0]["category"] == "Family Support"
