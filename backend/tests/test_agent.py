"""Tests for the agent loop with mocked Anthropic API."""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.models.user import User, UserProfile
from app.services.agent import SYSTEM_PROMPT, run_agent
from app.utils.auth import hash_password


def _create_user(db, name="Test User"):
    user = User(
        id=str(uuid.uuid4()),
        email="agent_test@example.com",
        password_hash=hash_password("password123"),
        name=name,
    )
    db.add(user)
    db.flush()
    profile = UserProfile(id=str(uuid.uuid4()), user_id=user.id, onboarding_complete=False)
    db.add(profile)
    db.commit()
    return user.id


def _make_text_response(text, stop_reason="end_turn"):
    """Create a mock Anthropic response with a text block."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    response = MagicMock()
    response.content = [block]
    response.stop_reason = stop_reason
    return response


def _make_tool_use_response(tool_name, tool_input, tool_id="tool_123"):
    """Create a mock Anthropic response with a tool_use block."""
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_id
    block.name = tool_name
    block.input = tool_input
    response = MagicMock()
    response.content = [block]
    response.stop_reason = "tool_use"
    return response


def _make_mixed_response(text, tool_name, tool_input, tool_id="tool_456"):
    """Create a mock response with both text and tool_use blocks."""
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = text

    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = tool_id
    tool_block.name = tool_name
    tool_block.input = tool_input

    response = MagicMock()
    response.content = [text_block, tool_block]
    response.stop_reason = "tool_use"
    return response


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------


def test_system_prompt_contains_key_sections():
    assert "personal financial advisor" in SYSTEM_PROMPT.lower()
    assert "Onboarding" in SYSTEM_PROMPT
    assert "Transaction Categories" in SYSTEM_PROMPT
    assert "CIBC" in SYSTEM_PROMPT
    assert "Uber Eats" in SYSTEM_PROMPT


# ---------------------------------------------------------------------------
# Simple text response (no tool use)
# ---------------------------------------------------------------------------


@patch("app.services.agent.settings")
@patch("app.services.agent.anthropic.Anthropic")
def test_agent_simple_text_response(mock_anthropic_cls, mock_settings, db):
    mock_settings.ANTHROPIC_API_KEY = "test-key"
    user_id = _create_user(db)

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_text_response(
        "Hello! I'm your financial advisor."
    )

    messages = [{"role": "user", "content": "Hi!"}]
    result = run_agent(messages, user_id, db)

    assert result == "Hello! I'm your financial advisor."
    mock_client.messages.create.assert_called_once()


# ---------------------------------------------------------------------------
# Single tool round-trip
# ---------------------------------------------------------------------------


@patch("app.services.agent.settings")
@patch("app.services.agent.anthropic.Anthropic")
def test_agent_single_tool_roundtrip(mock_anthropic_cls, mock_settings, db):
    mock_settings.ANTHROPIC_API_KEY = "test-key"
    user_id = _create_user(db)

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    # First call: agent wants to get profile
    tool_response = _make_tool_use_response("get_user_profile", {})
    # Second call: agent gives final text
    text_response = _make_text_response("I can see your profile. How can I help?")

    mock_client.messages.create.side_effect = [tool_response, text_response]

    messages = [{"role": "user", "content": "What's my financial situation?"}]
    result = run_agent(messages, user_id, db)

    assert "profile" in result.lower() or "help" in result.lower()
    assert mock_client.messages.create.call_count == 2


# ---------------------------------------------------------------------------
# Multi-tool round-trip
# ---------------------------------------------------------------------------


@patch("app.services.agent.settings")
@patch("app.services.agent.anthropic.Anthropic")
def test_agent_multi_tool_rounds(mock_anthropic_cls, mock_settings, db):
    mock_settings.ANTHROPIC_API_KEY = "test-key"
    user_id = _create_user(db)

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    # Round 1: get profile
    r1 = _make_tool_use_response("get_user_profile", {}, tool_id="t1")
    # Round 2: update profile
    r2 = _make_tool_use_response(
        "update_user_profile",
        {"net_monthly_income": 5000, "pay_frequency": "bi-weekly"},
        tool_id="t2",
    )
    # Round 3: final text
    r3 = _make_text_response("I've saved your income details!")

    mock_client.messages.create.side_effect = [r1, r2, r3]

    messages = [{"role": "user", "content": "My income is $5000 bi-weekly"}]
    result = run_agent(messages, user_id, db)

    assert "saved" in result.lower() or "income" in result.lower()
    assert mock_client.messages.create.call_count == 3

    # Verify the profile was actually updated in the DB
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    assert profile.net_monthly_income == 5000
    assert profile.pay_frequency == "bi-weekly"


# ---------------------------------------------------------------------------
# Mixed text + tool_use response
# ---------------------------------------------------------------------------


@patch("app.services.agent.settings")
@patch("app.services.agent.anthropic.Anthropic")
def test_agent_mixed_text_and_tool(mock_anthropic_cls, mock_settings, db):
    mock_settings.ANTHROPIC_API_KEY = "test-key"
    user_id = _create_user(db)

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    # First call: text + tool use
    mixed = _make_mixed_response(
        "Let me check your profile...",
        "get_user_profile",
        {},
    )
    # Second call: final answer
    final = _make_text_response("Here's what I found!")

    mock_client.messages.create.side_effect = [mixed, final]

    messages = [{"role": "user", "content": "Show me my profile"}]
    result = run_agent(messages, user_id, db)

    assert "found" in result.lower()
    assert mock_client.messages.create.call_count == 2


# ---------------------------------------------------------------------------
# No API key
# ---------------------------------------------------------------------------


@patch("app.services.agent.settings")
def test_agent_no_api_key(mock_settings, db):
    mock_settings.ANTHROPIC_API_KEY = ""
    user_id = _create_user(db)

    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        run_agent([{"role": "user", "content": "Hi"}], user_id, db)


# ---------------------------------------------------------------------------
# Max rounds exhausted
# ---------------------------------------------------------------------------


@patch("app.services.agent.MAX_TOOL_ROUNDS", 2)
@patch("app.services.agent.settings")
@patch("app.services.agent.anthropic.Anthropic")
def test_agent_max_rounds_exhausted(mock_anthropic_cls, mock_settings, db):
    mock_settings.ANTHROPIC_API_KEY = "test-key"
    user_id = _create_user(db)

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    # Always returns tool_use — never gives a final answer
    tool_resp = _make_tool_use_response("get_user_profile", {})
    mock_client.messages.create.return_value = tool_resp

    messages = [{"role": "user", "content": "Help me"}]
    result = run_agent(messages, user_id, db)

    # Should return fallback message
    assert result != ""
    assert mock_client.messages.create.call_count == 2


# ---------------------------------------------------------------------------
# Tool execution error is handled gracefully
# ---------------------------------------------------------------------------


@patch("app.services.agent.settings")
@patch("app.services.agent.anthropic.Anthropic")
def test_agent_tool_error_handled(mock_anthropic_cls, mock_settings, db):
    mock_settings.ANTHROPIC_API_KEY = "test-key"
    user_id = _create_user(db)

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    # Call an unknown tool — execute_tool returns {"error": ...}
    r1 = _make_tool_use_response("nonexistent_tool", {}, tool_id="t1")
    r2 = _make_text_response("Sorry, I encountered an issue.")

    mock_client.messages.create.side_effect = [r1, r2]

    messages = [{"role": "user", "content": "Do something weird"}]
    result = run_agent(messages, user_id, db)

    assert "issue" in result.lower() or "sorry" in result.lower()


# ---------------------------------------------------------------------------
# Messages are properly structured for Claude
# ---------------------------------------------------------------------------


@patch("app.services.agent.settings")
@patch("app.services.agent.anthropic.Anthropic")
def test_agent_passes_system_prompt(mock_anthropic_cls, mock_settings, db):
    mock_settings.ANTHROPIC_API_KEY = "test-key"
    user_id = _create_user(db)

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client
    mock_client.messages.create.return_value = _make_text_response("Hi!")

    run_agent([{"role": "user", "content": "Hello"}], user_id, db)

    call_kwargs = mock_client.messages.create.call_args
    assert call_kwargs.kwargs["system"] == SYSTEM_PROMPT
    assert call_kwargs.kwargs["model"] == "claude-sonnet-4-20250514"
    assert call_kwargs.kwargs["max_tokens"] == 4096
    assert len(call_kwargs.kwargs["tools"]) == 9


# ---------------------------------------------------------------------------
# Goal creation through agent
# ---------------------------------------------------------------------------


@patch("app.services.agent.settings")
@patch("app.services.agent.anthropic.Anthropic")
def test_agent_creates_goal(mock_anthropic_cls, mock_settings, db):
    mock_settings.ANTHROPIC_API_KEY = "test-key"
    user_id = _create_user(db)

    mock_client = MagicMock()
    mock_anthropic_cls.return_value = mock_client

    r1 = _make_tool_use_response(
        "create_goal",
        {"name": "Emergency Fund", "target_amount": 5000},
        tool_id="t1",
    )
    r2 = _make_text_response("I've created your Emergency Fund goal for $5,000!")

    mock_client.messages.create.side_effect = [r1, r2]

    messages = [{"role": "user", "content": "I want to save $5000 for emergencies"}]
    result = run_agent(messages, user_id, db)

    assert "Emergency Fund" in result or "5,000" in result

    # Verify goal was created in DB
    from app.models.goal import Goal

    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    assert len(goals) == 1
    assert goals[0].name == "Emergency Fund"
    assert goals[0].target_amount == 5000
