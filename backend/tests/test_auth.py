import jwt

from app.config import settings
from app.models.user import User, UserProfile


def test_register_success(client, db):
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "password_hash" not in data

    # Verify httpOnly cookie was set
    assert "access_token" in response.cookies

    # Verify token is valid
    token = response.cookies["access_token"]
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    assert payload["sub"] == data["id"]

    # Verify user and profile exist in DB
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
    response = client.post(
        "/auth/register",
        json={"email": "test@example.com"},
    )
    assert response.status_code == 422


def test_register_missing_email(client):
    response = client.post(
        "/auth/register",
        json={"password": "password123"},
    )
    assert response.status_code == 422
