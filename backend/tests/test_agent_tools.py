"""Unit tests for agent tool handler functions."""

import uuid

from app.models.transaction import Transaction
from app.models.user import User, UserProfile
from app.services.agent_tools import TOOL_DEFINITIONS, execute_tool
from app.utils.auth import hash_password


def _create_user(db, name="Test User", email="test@example.com"):
    """Create a test user with profile and return user_id."""
    user = User(
        id=str(uuid.uuid4()),
        email=email,
        password_hash=hash_password("password123"),
        name=name,
    )
    db.add(user)
    db.flush()

    profile = UserProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
        net_monthly_income=4634.42,
        pay_frequency="bi-weekly",
        fixed_expenses={"rent": 1200, "gym": 63},
        debts=[{"name": "Student Loan", "balance": 9000, "rate": 0, "minimum": 128.86}],
        budget_targets={"Groceries": 350, "Eating Out": 400},
        family_support_recipients=["Ammi"],
        emergency_fund=5000,
        risk_tolerance="medium",
        housing_situation="Living at home",
        financial_plan=None,
        onboarding_complete=False,
    )
    db.add(profile)
    db.commit()
    return user.id


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------


def test_tool_definitions_has_9_tools():
    assert len(TOOL_DEFINITIONS) == 9


def test_all_tools_have_required_fields():
    for tool in TOOL_DEFINITIONS:
        assert "name" in tool
        assert "description" in tool
        assert "input_schema" in tool
        assert tool["input_schema"]["type"] == "object"


# ---------------------------------------------------------------------------
# execute_tool dispatcher
# ---------------------------------------------------------------------------


def test_execute_unknown_tool(db):
    result = execute_tool("nonexistent_tool", {}, "fake-id", db)
    assert "error" in result
    assert "Unknown tool" in result["error"]


# ---------------------------------------------------------------------------
# get_user_profile
# ---------------------------------------------------------------------------


def test_get_user_profile(db):
    user_id = _create_user(db)
    result = execute_tool("get_user_profile", {}, user_id, db)

    assert result["name"] == "Test User"
    assert result["net_monthly_income"] == 4634.42
    assert result["pay_frequency"] == "bi-weekly"
    assert result["fixed_expenses"] == {"rent": 1200, "gym": 63}
    assert len(result["debts"]) == 1
    assert result["budget_targets"]["Groceries"] == 350
    assert result["family_support_recipients"] == ["Ammi"]
    assert result["emergency_fund"] == 5000
    assert result["risk_tolerance"] == "medium"
    assert result["housing_situation"] == "Living at home"
    assert result["onboarding_complete"] is False


def test_get_user_profile_not_found(db):
    result = execute_tool("get_user_profile", {}, "nonexistent-id", db)
    assert "error" in result


# ---------------------------------------------------------------------------
# update_user_profile
# ---------------------------------------------------------------------------


def test_update_user_profile_single_field(db):
    user_id = _create_user(db)
    result = execute_tool(
        "update_user_profile",
        {"net_monthly_income": 5000},
        user_id,
        db,
    )
    assert result["success"] is True
    assert "net_monthly_income" in result["updated_fields"]

    # Verify persistence
    profile = execute_tool("get_user_profile", {}, user_id, db)
    assert profile["net_monthly_income"] == 5000


def test_update_user_profile_multiple_fields(db):
    user_id = _create_user(db)
    result = execute_tool(
        "update_user_profile",
        {
            "risk_tolerance": "high",
            "emergency_fund": 10000,
            "housing_situation": "Renting",
        },
        user_id,
        db,
    )
    assert result["success"] is True
    assert len(result["updated_fields"]) == 3

    profile = execute_tool("get_user_profile", {}, user_id, db)
    assert profile["risk_tolerance"] == "high"
    assert profile["emergency_fund"] == 10000
    assert profile["housing_situation"] == "Renting"


def test_update_user_name(db):
    user_id = _create_user(db)
    result = execute_tool(
        "update_user_profile",
        {"name": "New Name"},
        user_id,
        db,
    )
    assert result["success"] is True

    profile = execute_tool("get_user_profile", {}, user_id, db)
    assert profile["name"] == "New Name"


def test_update_financial_plan(db):
    user_id = _create_user(db)
    plan = {
        "per_paycheck": {
            "savings": {"amount": 500, "pct": 21.6},
            "needs": {"amount": 1200, "pct": 51.8},
            "wants": {"amount": 617, "pct": 26.6},
        }
    }
    result = execute_tool(
        "update_user_profile",
        {"financial_plan": plan},
        user_id,
        db,
    )
    assert result["success"] is True

    profile = execute_tool("get_user_profile", {}, user_id, db)
    assert profile["financial_plan"]["per_paycheck"]["savings"]["amount"] == 500


def test_update_onboarding_complete(db):
    user_id = _create_user(db)
    result = execute_tool(
        "update_user_profile",
        {"onboarding_complete": True},
        user_id,
        db,
    )
    assert result["success"] is True

    profile = execute_tool("get_user_profile", {}, user_id, db)
    assert profile["onboarding_complete"] is True


def test_update_profile_not_found(db):
    result = execute_tool("update_user_profile", {"emergency_fund": 999}, "fake-id", db)
    assert "error" in result


# ---------------------------------------------------------------------------
# save_categorized_transactions
# ---------------------------------------------------------------------------


def test_save_transactions(db):
    user_id = _create_user(db)
    txns = [
        {
            "date": "2025-01-15",
            "description": "UBER EATS",
            "amount": 32.50,
            "category": "Uber Eats",
            "source": "debit",
        },
        {
            "date": "2025-01-16",
            "description": "LOBLAWS #1234",
            "amount": 85.00,
            "category": "Groceries",
            "source": "debit",
        },
    ]
    result = execute_tool("save_categorized_transactions", {"transactions": txns}, user_id, db)

    assert result["saved"] == 2
    assert result["duplicates_skipped"] == 0
    assert "2025-01" in result["months_affected"]


def test_save_transactions_dedup(db):
    user_id = _create_user(db)
    txn = {
        "date": "2025-01-15",
        "description": "UBER EATS",
        "amount": 32.50,
        "category": "Uber Eats",
        "source": "debit",
    }

    # Save once
    execute_tool("save_categorized_transactions", {"transactions": [txn]}, user_id, db)
    # Save again — should skip
    result = execute_tool("save_categorized_transactions", {"transactions": [txn]}, user_id, db)

    assert result["saved"] == 0
    assert result["duplicates_skipped"] == 1


def test_save_transactions_invalid_date(db):
    user_id = _create_user(db)
    txn = {
        "date": "not-a-date",
        "description": "BAD TXN",
        "amount": 10.0,
        "category": "Other",
        "source": "debit",
    }
    result = execute_tool("save_categorized_transactions", {"transactions": [txn]}, user_id, db)
    assert result["saved"] == 0


def test_save_transactions_multiple_months(db):
    user_id = _create_user(db)
    txns = [
        {
            "date": "2025-01-15",
            "description": "JAN TXN",
            "amount": 10.0,
            "category": "Other",
            "source": "debit",
        },
        {
            "date": "2025-02-15",
            "description": "FEB TXN",
            "amount": 20.0,
            "category": "Other",
            "source": "debit",
        },
    ]
    result = execute_tool("save_categorized_transactions", {"transactions": txns}, user_id, db)
    assert result["saved"] == 2
    assert sorted(result["months_affected"]) == ["2025-01", "2025-02"]


# ---------------------------------------------------------------------------
# get_transactions
# ---------------------------------------------------------------------------


def _seed_transactions(db, user_id):
    """Seed some transactions for query tests."""
    txns = [
        ("2025-01-10", "LOBLAWS", 85.00, "Groceries", "debit", "2025-01"),
        ("2025-01-15", "UBER EATS", 32.50, "Uber Eats", "debit", "2025-01"),
        ("2025-01-20", "AMAZON", 120.00, "Shopping", "credit_card", "2025-01"),
        ("2025-02-05", "METRO", 45.00, "Groceries", "debit", "2025-02"),
    ]
    for date, desc, amount, cat, source, mk in txns:
        from datetime import datetime

        db.add(
            Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=datetime.strptime(date, "%Y-%m-%d"),
                description=desc,
                amount=amount,
                category=cat,
                source=source,
                month_key=mk,
            )
        )
    db.commit()


def test_get_transactions_all(db):
    user_id = _create_user(db)
    _seed_transactions(db, user_id)

    result = execute_tool("get_transactions", {}, user_id, db)
    assert result["count"] == 4


def test_get_transactions_by_month(db):
    user_id = _create_user(db)
    _seed_transactions(db, user_id)

    result = execute_tool("get_transactions", {"month": "2025-01"}, user_id, db)
    assert result["count"] == 3


def test_get_transactions_by_category(db):
    user_id = _create_user(db)
    _seed_transactions(db, user_id)

    result = execute_tool("get_transactions", {"category": "Groceries"}, user_id, db)
    assert result["count"] == 2


def test_get_transactions_with_limit(db):
    user_id = _create_user(db)
    _seed_transactions(db, user_id)

    result = execute_tool("get_transactions", {"limit": 2}, user_id, db)
    assert result["count"] == 2


# ---------------------------------------------------------------------------
# get_spending_summary
# ---------------------------------------------------------------------------


def test_spending_summary(db):
    user_id = _create_user(db)
    _seed_transactions(db, user_id)

    result = execute_tool("get_spending_summary", {"month": "2025-01"}, user_id, db)
    assert result["month"] == "2025-01"
    assert result["by_category"]["Groceries"] == 85.00
    assert result["by_category"]["Uber Eats"] == 32.50
    assert result["by_category"]["Shopping"] == 120.00
    assert result["total"] == 237.50


def test_spending_summary_empty_month(db):
    user_id = _create_user(db)

    result = execute_tool("get_spending_summary", {"month": "2099-01"}, user_id, db)
    assert result["total"] == 0
    assert result["by_category"] == {}


# ---------------------------------------------------------------------------
# get_month_comparison
# ---------------------------------------------------------------------------


def test_month_comparison(db):
    user_id = _create_user(db)
    _seed_transactions(db, user_id)

    result = execute_tool(
        "get_month_comparison",
        {"month": "2025-02", "compare_to": "2025-01"},
        user_id,
        db,
    )
    assert result["current_month"]["month"] == "2025-02"
    assert result["previous_month"]["month"] == "2025-01"

    # Groceries: Feb=45, Jan=85 → diff=-40
    assert result["changes"]["Groceries"]["current"] == 45.00
    assert result["changes"]["Groceries"]["previous"] == 85.00
    assert result["changes"]["Groceries"]["diff"] == -40.00

    # Budget targets from profile
    assert result["budget_targets"]["Groceries"] == 350


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------


def test_create_goal(db):
    user_id = _create_user(db)

    result = execute_tool(
        "create_goal",
        {"name": "Emergency Fund", "target_amount": 5000},
        user_id,
        db,
    )
    assert result["success"] is True
    assert result["name"] == "Emergency Fund"
    assert result["target_amount"] == 5000
    assert result["status"] == "active"
    assert "id" in result


def test_create_goal_with_deadline(db):
    user_id = _create_user(db)

    result = execute_tool(
        "create_goal",
        {"name": "Vacation", "target_amount": 3000, "deadline": "2025-12-31"},
        user_id,
        db,
    )
    assert result["success"] is True


def test_get_goals(db):
    user_id = _create_user(db)
    execute_tool("create_goal", {"name": "Goal A", "target_amount": 1000}, user_id, db)
    execute_tool("create_goal", {"name": "Goal B", "target_amount": 2000}, user_id, db)

    result = execute_tool("get_goals", {}, user_id, db)
    assert len(result["goals"]) == 2


def test_get_goals_filter_status(db):
    user_id = _create_user(db)
    create_result = execute_tool(
        "create_goal", {"name": "Goal A", "target_amount": 1000}, user_id, db
    )
    execute_tool(
        "update_goal",
        {"goal_id": create_result["id"], "status": "completed"},
        user_id,
        db,
    )
    execute_tool("create_goal", {"name": "Goal B", "target_amount": 2000}, user_id, db)

    active = execute_tool("get_goals", {"status": "active"}, user_id, db)
    assert len(active["goals"]) == 1
    assert active["goals"][0]["name"] == "Goal B"

    completed = execute_tool("get_goals", {"status": "completed"}, user_id, db)
    assert len(completed["goals"]) == 1
    assert completed["goals"][0]["name"] == "Goal A"


def test_update_goal_progress(db):
    user_id = _create_user(db)
    create_result = execute_tool(
        "create_goal", {"name": "Savings", "target_amount": 5000}, user_id, db
    )
    goal_id = create_result["id"]

    result = execute_tool(
        "update_goal",
        {"goal_id": goal_id, "current_amount": 1500},
        user_id,
        db,
    )
    assert result["success"] is True

    goals = execute_tool("get_goals", {}, user_id, db)
    assert goals["goals"][0]["current_amount"] == 1500


def test_update_goal_not_found(db):
    user_id = _create_user(db)
    result = execute_tool(
        "update_goal",
        {"goal_id": "nonexistent"},
        user_id,
        db,
    )
    assert "error" in result


def test_update_goal_wrong_user(db):
    user_id = _create_user(db)
    create_result = execute_tool(
        "create_goal", {"name": "My Goal", "target_amount": 1000}, user_id, db
    )

    other_id = _create_user(db, name="Other", email="other@example.com")
    result = execute_tool(
        "update_goal",
        {"goal_id": create_result["id"], "current_amount": 999},
        other_id,
        db,
    )
    assert "error" in result
