from unittest.mock import MagicMock, patch


def _register_and_auth(client):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    token = resp.cookies["access_token"]
    client.cookies.set("access_token", token)


def _mock_anthropic_response(text: str):
    mock_content = MagicMock()
    mock_content.text = text
    mock_response = MagicMock()
    mock_response.content = [mock_content]
    return mock_response


def test_send_message(client):
    _register_and_auth(client)
    mock_resp = _mock_anthropic_response("Great question! Here's my advice.")

    with (
        patch("app.routers.chat.settings") as mock_settings,
        patch("app.routers.chat.anthropic.Anthropic") as mock_client_cls,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_resp
        mock_client_cls.return_value = mock_instance

        response = client.post("/chat", json={"message": "How am I doing?"})
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Great question! Here's my advice."


def test_chat_saves_history(client):
    _register_and_auth(client)
    mock_resp = _mock_anthropic_response("Saved reply")

    with (
        patch("app.routers.chat.settings") as mock_settings,
        patch("app.routers.chat.anthropic.Anthropic") as mock_client_cls,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_resp
        mock_client_cls.return_value = mock_instance

        client.post("/chat", json={"message": "Test message"})

    # Fetch history
    history_resp = client.get("/chat/history")
    assert history_resp.status_code == 200
    messages = history_resp.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Test message"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Saved reply"


def test_chat_context_includes_profile(client):
    _register_and_auth(client)
    client.put("/profile", json={"net_monthly_income": 5000, "budget_targets": {"Eating Out": 400}})

    mock_resp = _mock_anthropic_response("Noted your income.")

    with (
        patch("app.routers.chat.settings") as mock_settings,
        patch("app.routers.chat.anthropic.Anthropic") as mock_client_cls,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_resp
        mock_client_cls.return_value = mock_instance

        client.post("/chat", json={"message": "What are my targets?"})

        call_args = mock_instance.messages.create.call_args
        system_msg = call_args.kwargs["system"]
        assert "$5000.00" in system_msg
        assert "Eating Out" in system_msg


def test_chat_no_api_key(client):
    _register_and_auth(client)

    with patch("app.routers.chat.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = ""
        response = client.post("/chat", json={"message": "Hello"})
        assert response.status_code == 503


def test_clear_history(client):
    _register_and_auth(client)
    mock_resp = _mock_anthropic_response("Reply")

    with (
        patch("app.routers.chat.settings") as mock_settings,
        patch("app.routers.chat.anthropic.Anthropic") as mock_client_cls,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_resp
        mock_client_cls.return_value = mock_instance

        client.post("/chat", json={"message": "Hello"})

    # Clear
    clear_resp = client.delete("/chat/history")
    assert clear_resp.status_code == 204

    # Verify empty
    history_resp = client.get("/chat/history")
    assert len(history_resp.json()) == 0


def test_chat_unauthenticated(client):
    response = client.post("/chat", json={"message": "Hello"})
    assert response.status_code == 401


def test_get_history_unauthenticated(client):
    response = client.get("/chat/history")
    assert response.status_code == 401
