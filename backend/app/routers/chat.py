"""Chat router — unified endpoint for text messages and CSV uploads."""

import logging
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.chat import ChatMessage
from app.models.user import User
from app.schemas.chat import ChatMessageResponse, ChatResponse
from app.services.agent import run_agent
from app.services.csv_parser import parse_csv_raw
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_message(
    message: str = Form(""),
    files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Send a message (with optional CSV files) to the AI agent."""
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI advisor is not configured. Set ANTHROPIC_API_KEY.",
        )

    user_id = str(current_user.id)
    user_text = message.strip()

    # Parse any uploaded CSV files into raw transactions
    raw_transactions: list[dict[str, str]] = []
    file_names: list[str] = []
    for f in files:
        if f.filename and f.filename.lower().endswith(".csv"):
            content = await f.read()
            try:
                txns = parse_csv_raw(content, f.filename)
                raw_transactions.extend(txns)
                file_names.append(f.filename)
            except Exception:
                logger.exception("Failed to parse CSV: %s", f.filename)

    # Build the user content for the agent
    content_parts: list[str] = []
    if user_text:
        content_parts.append(user_text)
    if raw_transactions:
        content_parts.append(
            f"\n\n[Uploaded {len(raw_transactions)} transactions from: "
            f"{', '.join(file_names)}]\n\n"
            "Here are the raw transactions to categorize:\n\n"
            "| Date | Description | Amount | Source |\n"
            "|------|-------------|--------|--------|\n"
        )
        for txn in raw_transactions:
            content_parts.append(
                f"| {txn['date']} | {txn['description']} | ${txn['amount']} | {txn['source']} |"
            )

    combined_content = "\n".join(content_parts)

    if not combined_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a message or upload a CSV file.",
        )

    # Save user message to DB (the text the user typed, not the full context)
    display_message = user_text or f"[Uploaded {len(raw_transactions)} transactions]"
    user_msg = ChatMessage(user_id=user_id, role="user", content=display_message)
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

    # Build API messages — replace the last user message with the full content
    api_messages: list[dict[str, Any]] = []
    for msg in history[:-1]:  # All except the last (which we're replacing)
        role = str(msg.role)
        if role in ("user", "assistant"):
            api_messages.append({"role": role, "content": str(msg.content)})
    # Add the full content (with transaction data) as the latest user message
    api_messages.append({"role": "user", "content": combined_content})

    try:
        reply_text = run_agent(api_messages, user_id, db)
    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI advisor is not configured.",
        )
    except Exception:
        logger.exception("Agent failed")
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
