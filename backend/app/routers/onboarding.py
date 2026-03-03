from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.user import User, UserProfile
from app.utils.auth import get_current_user

router = APIRouter(prefix="/onboarding", tags=["onboarding"])

ONBOARDING_SYSTEM_PROMPT = """You are a friendly financial advisor helping a new user set up their profile.
You need to collect the following information one section at a time:

1. **Income**: net monthly income and pay frequency (weekly, bi-weekly, semi-monthly, monthly)
2. **Fixed Expenses**: recurring monthly bills (rent, subscriptions, loan payments, etc.)
3. **Debts**: outstanding debts with name, balance, interest rate, and minimum payment
4. **Budget Targets**: spending limits for categories like groceries, eating out, transportation, shopping, etc.
5. **Family Support**: any regular e-transfers/support to family members (names)
6. **Emergency Fund**: current savings amount set aside for emergencies
7. **Risk Tolerance**: low, medium, or high — how comfortable they are with financial risk

After collecting each section, respond with a JSON block in this exact format to save the data:
```json
{"profile_update": {"field_name": value}}
```

Rules:
- Ask about ONE section at a time
- Be conversational and warm, not robotic
- Give brief context about why each item matters
- If user says "skip", move to the next section
- When all sections are done, respond with: ```json
{"onboarding_complete": true}
```
- Keep responses concise (2-3 sentences + the question)
- For budget_targets, suggest common categories: Eating Out, Groceries, Transportation, Shopping, Entertainment
- For fixed_expenses, ask as a dictionary with descriptive keys
- For debts, collect as a list of objects with: name, balance, rate, minimum"""


class OnboardingMessage(BaseModel):
    message: str
    history: list[dict[str, str]] = []


class OnboardingResponse(BaseModel):
    reply: str
    profile_update: dict[str, Any] | None = None
    onboarding_complete: bool = False


def _extract_json_from_reply(reply: str) -> dict[str, Any] | None:
    """Extract JSON block from AI reply."""
    import json
    import re

    pattern = r"```json\s*(\{.*?\})\s*```"
    match = re.search(pattern, reply, re.DOTALL)
    if match:
        try:
            result: dict[str, Any] = json.loads(match.group(1))
            return result
        except json.JSONDecodeError:
            return None
    return None


def _clean_reply(reply: str) -> str:
    """Remove JSON blocks from the visible reply text."""
    import re

    return re.sub(r"```json\s*\{.*?\}\s*```", "", reply, flags=re.DOTALL).strip()


@router.post("/chat", response_model=OnboardingResponse)
def onboarding_chat(
    body: OnboardingMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not configured",
        )

    import anthropic

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    api_messages: list[anthropic.types.MessageParam] = []
    for m in body.history:
        role = m["role"]
        if role in ("user", "assistant"):
            api_messages.append(
                {"role": role, "content": m["content"]}  # type: ignore[typeddict-item]
            )
    api_messages.append({"role": "user", "content": body.message})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=ONBOARDING_SYSTEM_PROMPT,
        messages=api_messages,
    )

    reply = response.content[0].text  # type: ignore[union-attr]

    # Extract structured data
    extracted = _extract_json_from_reply(reply)
    profile_update = None
    onboarding_complete = False

    if extracted:
        if extracted.get("onboarding_complete"):
            onboarding_complete = True
            profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
            if profile:
                profile.onboarding_complete = True  # type: ignore[assignment]
                db.commit()
        elif "profile_update" in extracted:
            profile_update = extracted["profile_update"]
            profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
            if profile:
                for field, value in profile_update.items():
                    if hasattr(profile, field):
                        setattr(profile, field, value)
                db.commit()

    return OnboardingResponse(
        reply=_clean_reply(reply),
        profile_update=profile_update,
        onboarding_complete=onboarding_complete,
    )
