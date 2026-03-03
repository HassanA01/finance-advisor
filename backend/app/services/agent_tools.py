"""Agent tools — Claude tool_use definitions and database handler functions."""

import logging
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.goal import Goal
from app.models.transaction import Transaction
from app.models.user import UserProfile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tool definitions (passed to Claude's `tools` parameter)
# ---------------------------------------------------------------------------

TOOL_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "get_user_profile",
        "description": (
            "Retrieve the user's full financial profile including income, expenses, "
            "debts, budget targets, savings, risk tolerance, housing situation, and "
            "financial plan. Always call this before giving personalized advice."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "update_user_profile",
        "description": (
            "Update one or more fields on the user's financial profile. Use this to "
            "save information the user shares about their finances. Only include fields "
            "you want to change."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "User's first name"},
                "net_monthly_income": {
                    "type": "number",
                    "description": "Net monthly take-home pay",
                },
                "pay_frequency": {
                    "type": "string",
                    "enum": ["weekly", "bi-weekly", "semi-monthly", "monthly"],
                },
                "fixed_expenses": {
                    "type": "object",
                    "description": "Dict of expense_name -> monthly_amount",
                },
                "debts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "balance": {"type": "number"},
                            "rate": {"type": "number"},
                            "minimum": {"type": "number"},
                        },
                    },
                },
                "budget_targets": {
                    "type": "object",
                    "description": "Dict of category_name -> monthly_budget_amount",
                },
                "family_support_recipients": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "emergency_fund": {"type": "number"},
                "risk_tolerance": {"type": "string", "enum": ["low", "medium", "high"]},
                "housing_situation": {"type": "string"},
                "financial_plan": {
                    "type": "object",
                    "description": "Per-paycheck allocation plan with amounts and percentages",
                },
                "onboarding_complete": {"type": "boolean"},
            },
            "required": [],
        },
    },
    {
        "name": "save_categorized_transactions",
        "description": (
            "Save a list of categorized transactions to the database. Use this after "
            "the user confirms your categorization of their uploaded transactions. "
            "Duplicates (same date + description + amount) are automatically skipped."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "transactions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "YYYY-MM-DD"},
                            "description": {"type": "string"},
                            "amount": {"type": "number"},
                            "category": {"type": "string"},
                            "source": {
                                "type": "string",
                                "enum": ["debit", "credit_card"],
                            },
                        },
                        "required": ["date", "description", "amount", "category", "source"],
                    },
                },
            },
            "required": ["transactions"],
        },
    },
    {
        "name": "get_transactions",
        "description": "Query the user's transactions with optional filters.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "YYYY-MM format"},
                "category": {"type": "string"},
                "limit": {"type": "integer", "description": "Max rows to return (default 50)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_spending_summary",
        "description": "Get aggregated spending totals by category for a specific month.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "YYYY-MM format"},
            },
            "required": ["month"],
        },
    },
    {
        "name": "get_month_comparison",
        "description": (
            "Compare spending between two months, including differences by category "
            "and comparison against budget targets."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "Current month (YYYY-MM)"},
                "compare_to": {"type": "string", "description": "Previous month (YYYY-MM)"},
            },
            "required": ["month", "compare_to"],
        },
    },
    {
        "name": "get_goals",
        "description": "Get all of the user's financial goals.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by status (active, completed, paused)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "create_goal",
        "description": "Create a new financial goal for the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "target_amount": {"type": "number"},
                "deadline": {"type": "string", "description": "Optional deadline (YYYY-MM-DD)"},
            },
            "required": ["name", "target_amount"],
        },
    },
    {
        "name": "update_goal",
        "description": "Update an existing goal's progress or status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string"},
                "name": {"type": "string"},
                "target_amount": {"type": "number"},
                "current_amount": {"type": "number"},
                "deadline": {"type": "string"},
                "status": {"type": "string", "enum": ["active", "completed", "paused"]},
            },
            "required": ["goal_id"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool executor (central dispatcher)
# ---------------------------------------------------------------------------


def execute_tool(
    tool_name: str,
    tool_input: dict[str, Any],
    user_id: str,
    db: Session,
) -> dict[str, Any]:
    """Execute an agent tool and return the result as a dict."""
    handlers: dict[str, Any] = {
        "get_user_profile": _handle_get_user_profile,
        "update_user_profile": _handle_update_user_profile,
        "save_categorized_transactions": _handle_save_categorized_transactions,
        "get_transactions": _handle_get_transactions,
        "get_spending_summary": _handle_get_spending_summary,
        "get_month_comparison": _handle_get_month_comparison,
        "get_goals": _handle_get_goals,
        "create_goal": _handle_create_goal,
        "update_goal": _handle_update_goal,
    }
    handler = handlers.get(tool_name)
    if not handler:
        logger.warning("Unknown tool: %s", tool_name)
        return {"error": f"Unknown tool: {tool_name}"}
    try:
        return handler(tool_input, user_id, db)  # type: ignore[no-any-return]
    except Exception:
        logger.exception("Tool %s failed", tool_name)
        return {"error": f"Tool {tool_name} encountered an error"}


# ---------------------------------------------------------------------------
# Handler implementations
# ---------------------------------------------------------------------------


def _handle_get_user_profile(_input: dict[str, Any], user_id: str, db: Session) -> dict[str, Any]:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        return {"error": "Profile not found"}
    return {
        "name": profile.user.name if profile.user else None,
        "net_monthly_income": profile.net_monthly_income,
        "pay_frequency": profile.pay_frequency,
        "fixed_expenses": profile.fixed_expenses or {},
        "debts": profile.debts or [],
        "budget_targets": profile.budget_targets or {},
        "family_support_recipients": profile.family_support_recipients or [],
        "emergency_fund": float(profile.emergency_fund or 0),
        "risk_tolerance": profile.risk_tolerance or "medium",
        "housing_situation": profile.housing_situation,
        "financial_plan": profile.financial_plan,
        "onboarding_complete": bool(profile.onboarding_complete),
    }


def _handle_update_user_profile(
    tool_input: dict[str, Any], user_id: str, db: Session
) -> dict[str, Any]:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        return {"error": "Profile not found"}

    # Handle name separately — it lives on the User model
    if "name" in tool_input:
        profile.user.name = tool_input.pop("name")

    profile_fields = {
        "net_monthly_income",
        "pay_frequency",
        "fixed_expenses",
        "debts",
        "budget_targets",
        "family_support_recipients",
        "emergency_fund",
        "risk_tolerance",
        "housing_situation",
        "financial_plan",
        "onboarding_complete",
    }

    updated = []
    for field, value in tool_input.items():
        if field in profile_fields:
            setattr(profile, field, value)
            updated.append(field)

    db.commit()
    return {"updated_fields": updated, "success": True}


def _handle_save_categorized_transactions(
    tool_input: dict[str, Any], user_id: str, db: Session
) -> dict[str, Any]:
    transactions = tool_input.get("transactions", [])
    saved = 0
    duplicates_skipped = 0
    months_affected: set[str] = set()

    for txn in transactions:
        try:
            date = datetime.strptime(txn["date"], "%Y-%m-%d")
        except (ValueError, KeyError):
            logger.warning("Skipping transaction with invalid date: %s", txn)
            continue

        description = str(txn.get("description", "")).strip()
        amount = float(txn.get("amount", 0))
        category = str(txn.get("category", "Other"))
        source = str(txn.get("source", "debit"))
        month_key = date.strftime("%Y-%m")

        # Dedup check
        existing = (
            db.query(Transaction)
            .filter(
                Transaction.user_id == user_id,
                Transaction.date == date,
                Transaction.description == description,
                Transaction.amount == amount,
            )
            .first()
        )
        if existing:
            duplicates_skipped += 1
            continue

        db.add(
            Transaction(
                id=str(uuid.uuid4()),
                user_id=user_id,
                date=date,
                description=description,
                amount=round(amount, 2),
                category=category,
                source=source,
                month_key=month_key,
            )
        )
        saved += 1
        months_affected.add(month_key)

    db.commit()
    return {
        "saved": saved,
        "duplicates_skipped": duplicates_skipped,
        "months_affected": sorted(months_affected),
    }


def _handle_get_transactions(
    tool_input: dict[str, Any], user_id: str, db: Session
) -> dict[str, Any]:
    query = db.query(Transaction).filter(Transaction.user_id == user_id)

    if month := tool_input.get("month"):
        query = query.filter(Transaction.month_key == month)
    if category := tool_input.get("category"):
        query = query.filter(Transaction.category == category)

    limit = tool_input.get("limit", 50)
    rows = query.order_by(Transaction.date.desc()).limit(limit).all()

    return {
        "transactions": [
            {
                "date": t.date.strftime("%Y-%m-%d") if t.date else "",
                "description": t.description,
                "amount": float(t.amount),
                "category": t.category,
                "source": t.source,
                "month_key": t.month_key,
            }
            for t in rows
        ],
        "count": len(rows),
    }


def _handle_get_spending_summary(
    tool_input: dict[str, Any], user_id: str, db: Session
) -> dict[str, Any]:
    month = tool_input.get("month", "")
    rows = (
        db.query(Transaction.category, func.sum(Transaction.amount))
        .filter(Transaction.user_id == user_id, Transaction.month_key == month)
        .group_by(Transaction.category)
        .all()
    )
    by_category = {cat: round(float(total), 2) for cat, total in rows}
    total = round(sum(by_category.values()), 2)
    return {"month": month, "total": total, "by_category": by_category}


def _handle_get_month_comparison(
    tool_input: dict[str, Any], user_id: str, db: Session
) -> dict[str, Any]:
    month_a = tool_input.get("month", "")
    month_b = tool_input.get("compare_to", "")

    def _aggregate(m: str) -> dict[str, float]:
        rows = (
            db.query(Transaction.category, func.sum(Transaction.amount))
            .filter(Transaction.user_id == user_id, Transaction.month_key == m)
            .group_by(Transaction.category)
            .all()
        )
        return {cat: round(float(total), 2) for cat, total in rows}

    current = _aggregate(month_a)
    previous = _aggregate(month_b)

    all_cats = set(current.keys()) | set(previous.keys())
    changes: dict[str, dict[str, float]] = {}
    for cat in sorted(all_cats):
        cur = current.get(cat, 0.0)
        prev = previous.get(cat, 0.0)
        changes[cat] = {"current": cur, "previous": prev, "diff": round(cur - prev, 2)}

    # Include budget targets
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    targets = {}
    if profile and profile.budget_targets:
        targets = {k: float(v) for k, v in profile.budget_targets.items()}

    return {
        "current_month": {"month": month_a, "total": sum(current.values()), "by_category": current},
        "previous_month": {
            "month": month_b,
            "total": sum(previous.values()),
            "by_category": previous,
        },
        "changes": changes,
        "budget_targets": targets,
    }


def _handle_get_goals(tool_input: dict[str, Any], user_id: str, db: Session) -> dict[str, Any]:
    query = db.query(Goal).filter(Goal.user_id == user_id)
    if status := tool_input.get("status"):
        query = query.filter(Goal.status == status)

    goals = query.order_by(Goal.created_at.desc()).all()
    return {
        "goals": [
            {
                "id": str(g.id),
                "name": g.name,
                "target_amount": float(g.target_amount),
                "current_amount": float(g.current_amount),
                "deadline": g.deadline.strftime("%Y-%m-%d") if g.deadline else None,
                "status": g.status,
            }
            for g in goals
        ]
    }


def _handle_create_goal(tool_input: dict[str, Any], user_id: str, db: Session) -> dict[str, Any]:
    deadline = None
    if dl := tool_input.get("deadline"):
        try:
            deadline = datetime.strptime(dl, "%Y-%m-%d")
        except ValueError:
            pass

    goal = Goal(
        id=str(uuid.uuid4()),
        user_id=user_id,
        name=tool_input["name"],
        target_amount=float(tool_input["target_amount"]),
        deadline=deadline,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return {
        "id": str(goal.id),
        "name": goal.name,
        "target_amount": float(goal.target_amount),
        "status": goal.status,
        "success": True,
    }


def _handle_update_goal(tool_input: dict[str, Any], user_id: str, db: Session) -> dict[str, Any]:
    goal = db.query(Goal).filter(Goal.id == tool_input["goal_id"], Goal.user_id == user_id).first()
    if not goal:
        return {"error": "Goal not found"}

    for field in ("name", "target_amount", "current_amount", "status"):
        if field in tool_input:
            setattr(goal, field, tool_input[field])
    if "deadline" in tool_input:
        try:
            goal.deadline = datetime.strptime(tool_input["deadline"], "%Y-%m-%d")  # type: ignore[assignment]
        except (ValueError, TypeError):
            pass

    db.commit()
    return {"id": str(goal.id), "name": goal.name, "status": goal.status, "success": True}
