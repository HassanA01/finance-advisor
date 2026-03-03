# DEPRECATED: Monthly analysis is now handled by the AI agent
# (app/services/agent.py). This file is kept for the reports router
# which still uses analyze_month() for report generation.

import json
import logging
from typing import Any

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a personal finance advisor. You are fiduciary-minded, empathetic, and \
focused on sustainable improvement rather than dramatic overhauls.

Your client tends to burn out on intense short-term changes. Always recommend gradual, \
achievable steps. Celebrate progress, even small wins.

When analyzing monthly spending:
1. Compare spending against budget targets — highlight categories over/under budget
2. Compare against previous month — note meaningful trends (not noise)
3. Provide 3-5 specific, actionable insights
4. Keep the tone encouraging but honest
5. Use specific dollar amounts from the data

Respond in JSON format with two fields:
- "summary": A narrative paragraph (2-4 sentences) summarizing the month's spending
- "insights": A list of 3-5 brief bullet-point strings with specific observations and suggestions
"""


def analyze_month(
    spending: dict[str, float],
    vs_target: dict[str, Any],
    vs_prev_month: dict[str, Any],
    profile_context: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    """Generate AI analysis of monthly spending. Returns (summary, insights)."""
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set — skipping AI analysis")
        return "", []

    user_message = _build_user_message(spending, vs_target, vs_prev_month, profile_context)

    try:
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text  # type: ignore[union-attr]
        return _parse_response(text)
    except Exception:
        logger.exception("AI analysis failed")
        return "", []


def _build_user_message(
    spending: dict[str, float],
    vs_target: dict[str, Any],
    vs_prev_month: dict[str, Any],
    profile_context: dict[str, Any] | None = None,
) -> str:
    """Build the user message with spending data for the AI."""
    parts: list[str] = []

    total = sum(spending.values())
    parts.append(f"Total spending this month: ${total:.2f}")
    parts.append("")

    parts.append("Spending by category:")
    for cat, amount in sorted(spending.items(), key=lambda x: -x[1]):
        parts.append(f"  {cat}: ${amount:.2f}")
    parts.append("")

    if vs_target:
        parts.append("Budget targets comparison:")
        for cat, info in sorted(vs_target.items()):
            diff = info.get("diff", 0)
            target = info.get("target", 0)
            actual = info.get("actual", 0)
            status = "OVER" if diff > 0 else "under"
            parts.append(f"  {cat}: ${actual:.2f} / ${target:.2f} ({status} by ${abs(diff):.2f})")
        parts.append("")

    if vs_prev_month:
        parts.append("Month-over-month comparison:")
        for cat, info in sorted(vs_prev_month.items()):
            cur = info.get("current", 0)
            prev = info.get("previous", 0)
            diff = info.get("diff", 0)
            if prev > 0:
                direction = "up" if diff > 0 else "down"
                parts.append(f"  {cat}: ${cur:.2f} (was ${prev:.2f}, {direction} ${abs(diff):.2f})")
        parts.append("")

    if profile_context:
        income = profile_context.get("net_monthly_income")
        if income:
            parts.append(f"Monthly income: ${income:.2f}")
            parts.append(f"Spending as % of income: {total / income * 100:.1f}%")

    parts.append("")
    parts.append("Please analyze this month's spending and provide your JSON response.")

    return "\n".join(parts)


def _parse_response(text: str) -> tuple[str, list[str]]:
    """Parse the AI response JSON into (summary, insights)."""
    # Try to extract JSON from the response
    try:
        # Handle case where response is wrapped in markdown code block
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            # Remove first and last lines (```json and ```)
            json_str = "\n".join(lines[1:-1])
        else:
            json_str = cleaned

        data: dict[str, Any] = json.loads(json_str)
        summary = str(data.get("summary", ""))
        insights = [str(i) for i in data.get("insights", [])]
        return summary, insights
    except (json.JSONDecodeError, KeyError, IndexError):
        logger.warning("Failed to parse AI response as JSON, using raw text")
        return text.strip(), []
