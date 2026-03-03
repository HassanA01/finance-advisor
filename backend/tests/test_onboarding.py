from unittest.mock import MagicMock, patch


def _register_and_auth(client):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    token = resp.cookies["access_token"]
    client.cookies.set("access_token", token)


def _mock_anthropic_response(text):
    mock_content = MagicMock()
    mock_content.text = text
    mock_message = MagicMock()
    mock_message.content = [mock_content]
    return mock_message


def test_onboarding_chat_unauthenticated(client):
    response = client.post("/onboarding/chat", json={"message": "hello"})
    assert response.status_code == 401


def test_onboarding_chat_no_api_key(client):
    _register_and_auth(client)
    with patch("app.routers.onboarding.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = ""
        response = client.post("/onboarding/chat", json={"message": "hello"})
        assert response.status_code == 503


def test_onboarding_chat_basic(client):
    _register_and_auth(client)
    mock_resp = _mock_anthropic_response(
        "Welcome! Let's start with your income. What is your net monthly income?"
    )

    with (
        patch("app.routers.onboarding.settings") as mock_settings,
        patch("anthropic.Anthropic") as mock_client_cls,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_resp
        mock_client_cls.return_value = mock_instance

        response = client.post("/onboarding/chat", json={"message": "Hi, let's start"})
        assert response.status_code == 200
        data = response.json()
        assert "income" in data["reply"].lower()
        assert data["profile_update"] is None
        assert data["onboarding_complete"] is False


def test_onboarding_chat_with_profile_update(client):
    _register_and_auth(client)
    mock_resp = _mock_anthropic_response(
        'Great! I\'ve noted that down.\n```json\n{"profile_update": {"net_monthly_income": 4634.42, "pay_frequency": "bi-weekly"}}\n```\nNow let\'s talk about your fixed expenses.'
    )

    with (
        patch("app.routers.onboarding.settings") as mock_settings,
        patch("anthropic.Anthropic") as mock_client_cls,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_resp
        mock_client_cls.return_value = mock_instance

        response = client.post(
            "/onboarding/chat",
            json={"message": "I make $4634.42 and get paid bi-weekly"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["profile_update"]["net_monthly_income"] == 4634.42
        assert data["profile_update"]["pay_frequency"] == "bi-weekly"

    # Verify profile was updated in DB
    profile_resp = client.get("/profile")
    assert profile_resp.json()["net_monthly_income"] == 4634.42


def test_onboarding_chat_complete(client):
    _register_and_auth(client)
    mock_resp = _mock_anthropic_response(
        'Your profile is all set up!\n```json\n{"onboarding_complete": true}\n```'
    )

    with (
        patch("app.routers.onboarding.settings") as mock_settings,
        patch("anthropic.Anthropic") as mock_client_cls,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_resp
        mock_client_cls.return_value = mock_instance

        response = client.post(
            "/onboarding/chat",
            json={"message": "That's everything"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["onboarding_complete"] is True

    # Verify onboarding_complete flag set in DB
    profile_resp = client.get("/profile")
    assert profile_resp.json()["onboarding_complete"] is True
