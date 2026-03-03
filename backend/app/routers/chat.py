import logging
from typing import Any

import anthropic
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.chat import ChatMessage
from app.models.goal import Goal
from app.models.transaction import Transaction
from app.models.user import User, UserProfile
from app.schemas.chat import ChatMessageResponse, ChatRequest, ChatResponse
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

SYSTEM_PROMPT = """You are a personal finance advisor for a user who banks with CIBC in Canada. \
You are fiduciary-minded, empathetic, and focused on sustainable improvement.

Key principles:
- This user tends to burn out on intense short-term changes. Always recommend gradual steps.
- Celebrate progress, even small wins. Never shame spending.
- Use specific numbers from their data when available.
- Be conversational and warm, not robotic.
- Keep responses concise — 2-4 paragraphs max unless asked for detail.
- If you don't have enough data, say so rather than guessing.

You have access to the user's financial context below. Use it to give personalized advice.
"""


def _build_context(db: Session, user_id: str) -> str:
    """Build financial context string for the AI."""
    parts: list[str] = []

    # Profile
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if profile:
        if profile.net_monthly_income:
            parts.append(f"Monthly income: ${profile.net_monthly_income:.2f}")
        if profile.pay_frequency:
            parts.append(f"Pay frequency: {profile.pay_frequency}")
        if profile.fixed_expenses:
            total_fixed = sum(float(v) for v in profile.fixed_expenses.values())
            parts.append(f"Fixed monthly expenses: ${total_fixed:.2f}")
            expenses = ", ".join(f"{k}: ${float(v):.2f}" for k, v in profile.fixed_expenses.items())
            parts.append(f"  Breakdown: {expenses}")
        if profile.budget_targets:
            parts.append("Budget targets:")
            for cat, target in profile.budget_targets.items():
                parts.append(f"  {cat}: ${float(target):.2f}")
        if profile.emergency_fund:
            parts.append(f"Emergency fund: ${profile.emergency_fund:.2f}")

    # Recent spending (last 2 months)
    recent_months = (
        db.query(Transaction.month_key)
        .filter(Transaction.user_id == user_id)
        .distinct()
        .order_by(Transaction.month_key.desc())
        .limit(2)
        .all()
    )
    for (month_key,) in recent_months:
        rows: list[Any] = (
            db.query(Transaction.category, func.sum(Transaction.amount))
            .filter(Transaction.user_id == user_id, Transaction.month_key == month_key)
            .group_by(Transaction.category)
            .all()
        )
        if rows:
            total = sum(float(amt) for _, amt in rows)
            parts.append(f"\nSpending for {month_key} (total: ${total:.2f}):")
            for cat, amt in sorted(rows, key=lambda x: -float(x[1])):
                parts.append(f"  {cat}: ${float(amt):.2f}")

    # Goals
    goals = db.query(Goal).filter(Goal.user_id == user_id, Goal.status == "active").all()
    if goals:
        parts.append("\nActive goals:")
        for g in goals:
            pct = (float(g.current_amount) / float(g.target_amount) * 100) if g.target_amount else 0
            parts.append(
                f"  {g.name}: ${float(g.current_amount):.2f} / ${float(g.target_amount):.2f} ({pct:.0f}%)"
            )

    return "\n".join(parts) if parts else "No financial data available yet."


@router.post("", response_model=ChatResponse)
def send_message(
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Send a message to the AI advisor and get a response."""
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI advisor is not configured. Set ANTHROPIC_API_KEY.",
        )

    user_id = str(current_user.id)

    # Save user message
    user_msg = ChatMessage(user_id=user_id, role="user", content=body.message)
    db.add(user_msg)
    db.commit()

    # Build conversation history (last 20 messages for context)
    history = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(20)
        .all()
    )
    history.reverse()

    # Build API messages
    context = _build_context(db, user_id)
    system = f"{SYSTEM_PROMPT}\n\n--- USER'S FINANCIAL CONTEXT ---\n{context}"

    api_messages: list[anthropic.types.MessageParam] = []
    for msg in history:
        role = str(msg.role)
        if role in ("user", "assistant"):
            api_messages.append({"role": role, "content": str(msg.content)})  # type: ignore[typeddict-item]

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=system,
            messages=api_messages,
        )
        reply_text = response.content[0].text  # type: ignore[union-attr]
    except Exception:
        logger.exception("AI chat failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI advisor is temporarily unavailable. Please try again.",
        )

    # Save assistant response
    assistant_msg = ChatMessage(user_id=user_id, role="assistant", content=reply_text)
    db.add(assistant_msg)
    db.commit()

    return ChatResponse(reply=reply_text)


@router.get("/history", response_model=list[ChatMessageResponse])
def get_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ChatMessageResponse]:
    """Get chat history for the current user."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == str(current_user.id))
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.delete("/history", status_code=status.HTTP_204_NO_CONTENT)
def clear_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Clear chat history for the current user."""
    db.query(ChatMessage).filter(ChatMessage.user_id == str(current_user.id)).delete()
    db.commit()
