from unittest.mock import MagicMock, patch


def _register_and_auth(client):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    token = resp.cookies["access_token"]
    client.cookies.set("access_token", token)


def _mock_anthropic_response(text):
    mock_message = MagicMock()
    mock_content = MagicMock()
    mock_content.text = text
    mock_message.content = [mock_content]
    return mock_message


def test_onboarding_chat_unauthenticated(client):
    response = client.post("/onboarding/chat", json={"message": "hello"})
    assert response.status_code == 401


@patch("app.routers.onboarding.settings")
def test_onboarding_chat_no_api_key(mock_settings, client):
    _register_and_auth(client)
    mock_settings.ANTHROPIC_API_KEY = ""
    response = client.post("/onboarding/chat", json={"message": "hello"})
    assert response.status_code == 503


@patch("app.routers.onboarding.anthropic")
@patch("app.routers.onboarding.settings")
def test_onboarding_chat_basic(mock_settings, mock_anthropic, client):
    _register_and_auth(client)
    mock_settings.ANTHROPIC_API_KEY = "test-key"
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = _mock_anthropic_response(
        "Welcome! Let's start with your income. What is your net monthly income?"
    )

    response = client.post("/onboarding/chat", json={"message": "Hi, let's start"})
    assert response.status_code == 200
    data = response.json()
    assert "income" in data["reply"].lower()
    assert data["profile_update"] is None
    assert data["onboarding_complete"] is False


@patch("app.routers.onboarding.anthropic")
@patch("app.routers.onboarding.settings")
def test_onboarding_chat_with_profile_update(mock_settings, mock_anthropic, client):
    _register_and_auth(client)
    mock_settings.ANTHROPIC_API_KEY = "test-key"
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = _mock_anthropic_response(
        'Great! I\'ve noted that down.\n```json\n{"profile_update": {"net_monthly_income": 4634.42, "pay_frequency": "bi-weekly"}}\n```\nNow let\'s talk about your fixed expenses.'
    )

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


@patch("app.routers.onboarding.anthropic")
@patch("app.routers.onboarding.settings")
def test_onboarding_chat_complete(mock_settings, mock_anthropic, client):
    _register_and_auth(client)
    mock_settings.ANTHROPIC_API_KEY = "test-key"
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_client.messages.create.return_value = _mock_anthropic_response(
        'Your profile is all set up!\n```json\n{"onboarding_complete": true}\n```'
    )

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
