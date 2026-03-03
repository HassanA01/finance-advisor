import io
import json
from unittest.mock import MagicMock, patch


def _register_and_auth(client):
    resp = client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "securepassword123"},
    )
    token = resp.cookies["access_token"]
    client.cookies.set("access_token", token)


def _upload(client, csv_content, filename="test.csv"):
    return client.post(
        "/transactions/upload",
        files=[("files", (filename, io.BytesIO(csv_content.encode()), "text/csv"))],
    )


JAN_CSV = """Date,Transaction,Debit,Credit
2024-01-15,TIM HORTONS #123,5.50,
2024-01-16,UBER EATS,25.00,
2024-01-17,METRO GROCERY,45.00,
"""


def _mock_anthropic_response(summary: str, insights: list[str]):
    """Create a mock Anthropic API response."""
    mock_content = MagicMock()
    mock_content.text = json.dumps({"summary": summary, "insights": insights})

    mock_response = MagicMock()
    mock_response.content = [mock_content]
    return mock_response


def test_analyze_month_generates_summary(client):
    _register_and_auth(client)
    _upload(client, JAN_CSV)

    mock_resp = _mock_anthropic_response(
        "You spent $75.50 this month across 3 categories.",
        ["Eating out is well under budget.", "Groceries spending looks healthy."],
    )

    with (
        patch("app.services.advisor.settings") as mock_settings,
        patch("app.services.advisor.anthropic.Anthropic") as mock_client_cls,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_resp
        mock_client_cls.return_value = mock_instance

        response = client.get("/reports/2024-01")
        assert response.status_code == 200
        data = response.json()
        assert data["summary"] == "You spent $75.50 this month across 3 categories."
        assert len(data["insights"]) == 2
        assert "Eating out" in data["insights"][0]


def test_analyze_month_prompt_contains_data(client):
    _register_and_auth(client)
    _upload(client, JAN_CSV)
    client.put("/profile", json={"budget_targets": {"Eating Out": 20.00}})

    mock_resp = _mock_anthropic_response("Summary", ["Insight"])

    with (
        patch("app.services.advisor.settings") as mock_settings,
        patch("app.services.advisor.anthropic.Anthropic") as mock_client_cls,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_resp
        mock_client_cls.return_value = mock_instance

        client.get("/reports/2024-01")

        # Verify the prompt was constructed with spending data
        call_args = mock_instance.messages.create.call_args
        user_msg = call_args.kwargs["messages"][0]["content"]
        assert "Eating Out" in user_msg
        assert "Groceries" in user_msg
        assert "Budget targets" in user_msg


def test_analyze_month_no_api_key(client):
    _register_and_auth(client)
    _upload(client, JAN_CSV)

    with patch("app.services.advisor.settings") as mock_settings:
        mock_settings.ANTHROPIC_API_KEY = ""

        response = client.get("/reports/2024-01")
        assert response.status_code == 200
        data = response.json()
        # Should still work but without AI analysis
        assert data["summary"] is None
        assert data["insights"] == [] or data["insights"] is None


def test_analyze_month_api_failure(client):
    _register_and_auth(client)
    _upload(client, JAN_CSV)

    with (
        patch("app.services.advisor.settings") as mock_settings,
        patch("app.services.advisor.anthropic.Anthropic") as mock_client_cls,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_instance = MagicMock()
        mock_instance.messages.create.side_effect = Exception("API error")
        mock_client_cls.return_value = mock_instance

        response = client.get("/reports/2024-01")
        assert response.status_code == 200
        data = response.json()
        # Graceful fallback — report still works without AI
        assert data["total_spent"] > 0


def test_analyze_month_markdown_json_response(client):
    """Test parsing when AI wraps JSON in markdown code block."""
    _register_and_auth(client)
    _upload(client, JAN_CSV)

    mock_content = MagicMock()
    mock_content.text = '```json\n{"summary": "Wrapped summary", "insights": ["Point 1"]}\n```'
    mock_response = MagicMock()
    mock_response.content = [mock_content]

    with (
        patch("app.services.advisor.settings") as mock_settings,
        patch("app.services.advisor.anthropic.Anthropic") as mock_client_cls,
    ):
        mock_settings.ANTHROPIC_API_KEY = "test-key"
        mock_instance = MagicMock()
        mock_instance.messages.create.return_value = mock_response
        mock_client_cls.return_value = mock_instance

        response = client.get("/reports/2024-01")
        data = response.json()
        assert data["summary"] == "Wrapped summary"
        assert data["insights"] == ["Point 1"]
