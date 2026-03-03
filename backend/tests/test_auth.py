import jwt

from app.config import settings
from app.models.user import User, UserProfile


def _register(client, email="test@example.com", password="securepassword123"):
    return client.post("/auth/register", json={"email": email, "password": password})


def test_register_success(client, db):
    response = _register(client)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password_hash" not in data

    assert "access_token" in response.cookies

    token = response.cookies["access_token"]
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == data["id"]

    user = db.query(User).filter(User.email == "test@example.com").first()
    assert user is not None

    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    assert profile is not None
    assert profile.onboarding_complete is False


def test_register_duplicate_email(client):
    payload = {"email": "dupe@example.com", "password": "password123"}
    client.post("/auth/register", json=payload)

    response = client.post("/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_register_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "password123"},
    )
    assert response.status_code == 422


def test_register_missing_password(client):
    response = client.post("/auth/register", json={"email": "test@example.com"})
    assert response.status_code == 422


def test_register_missing_email(client):
    response = client.post("/auth/register", json={"password": "password123"})
    assert response.status_code == 422


# --- Login tests ---


def test_login_success(client):
    _register(client)
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
    assert "access_token" in response.cookies


def test_login_wrong_password(client):
    _register(client)
    response = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 401


# --- /auth/me tests ---


def test_me_authenticated(client):
    reg = _register(client)
    token = reg.cookies["access_token"]
    client.cookies.set("access_token", token)

    response = client.get("/auth/me")
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"


def test_me_unauthenticated(client):
    response = client.get("/auth/me")
    assert response.status_code == 401


# --- Logout tests ---


def test_logout_clears_cookie(client):
    _register(client)
    response = client.post("/auth/logout")
    assert response.status_code == 204
    assert response.cookies.get("access_token") is not None  # delete cookie header present
