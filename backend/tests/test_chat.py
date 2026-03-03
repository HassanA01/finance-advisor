"""Tests for the unified chat endpoint (FormData + agent)."""

import io
from unittest.mock import patch


def _register_and_auth(client):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    token = resp.cookies["access_token"]
    client.cookies.set("access_token", token)


def test_send_message(client):
    _register_and_auth(client)

    with patch("app.routers.chat.run_agent", return_value="Great question! Here's my advice."):
        response = client.post("/chat", data={"message": "How am I doing?"})
        assert response.status_code == 200
        data = response.json()
        assert data["reply"] == "Great question! Here's my advice."


def test_chat_saves_history(client):
    _register_and_auth(client)

    with patch("app.routers.chat.run_agent", return_value="Saved reply"):
        client.post("/chat", data={"message": "Test message"})

    history_resp = client.get("/chat/history")
    assert history_resp.status_code == 200
    messages = history_resp.json()
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Test message"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Saved reply"


def test_chat_with_csv_upload(client):
    _register_and_auth(client)

    csv_content = b"2025-01-15,LOBLAWS #1234,85.00,\n2025-01-16,UBER EATS,32.50,\n"
    csv_file = io.BytesIO(csv_content)

    with patch("app.routers.chat.run_agent", return_value="I see 2 transactions.") as mock_agent:
        response = client.post(
            "/chat",
            data={"message": "Please categorize these"},
            files=[("files", ("transactions.csv", csv_file, "text/csv"))],
        )
        assert response.status_code == 200
        assert "2 transactions" in response.json()["reply"]

        # Verify the agent received transaction data in the message
        call_args = mock_agent.call_args
        messages = call_args[0][0]  # First positional arg
        last_msg = messages[-1]["content"]
        assert "LOBLAWS" in last_msg
        assert "UBER EATS" in last_msg


def test_chat_csv_only_no_text(client):
    _register_and_auth(client)

    csv_content = b"2025-01-15,METRO,45.00,\n"
    csv_file = io.BytesIO(csv_content)

    with patch("app.routers.chat.run_agent", return_value="Categorized!"):
        response = client.post(
            "/chat",
            data={"message": ""},
            files=[("files", ("jan.csv", csv_file, "text/csv"))],
        )
        assert response.status_code == 200

    # History should show a descriptive message, not empty
    history = client.get("/chat/history").json()
    assert "[Uploaded" in history[0]["content"]


def test_chat_empty_request(client):
    _register_and_auth(client)

    response = client.post("/chat", data={"message": ""})
    assert response.status_code == 400


def test_chat_no_api_key(client):
    _register_and_auth(client)

    with patch("app.routers.chat.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = ""
        response = client.post("/chat", data={"message": "Hello"})
        assert response.status_code == 503


def test_clear_history(client):
    _register_and_auth(client)

    with patch("app.routers.chat.run_agent", return_value="Reply"):
        client.post("/chat", data={"message": "Hello"})

    clear_resp = client.delete("/chat/history")
    assert clear_resp.status_code == 204

    history_resp = client.get("/chat/history")
    assert len(history_resp.json()) == 0


def test_chat_unauthenticated(client):
    response = client.post("/chat", data={"message": "Hello"})
    assert response.status_code == 401


def test_get_history_unauthenticated(client):
    response = client.get("/chat/history")
    assert response.status_code == 401


def test_agent_error_returns_502(client):
    _register_and_auth(client)

    with patch("app.routers.chat.run_agent", side_effect=Exception("API error")):
        response = client.post("/chat", data={"message": "Hello"})
        assert response.status_code == 502
