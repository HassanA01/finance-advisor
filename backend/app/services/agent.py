"""AI financial advisor agent with Claude tool_use loop."""

import json
import logging
from typing import Any

import anthropic

from app.config import settings
from app.services.agent_tools import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)

MAX_TOOL_ROUNDS = 10
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 4096

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are a personal financial advisor agent. You have FULL read/write access to \
the user's financial database through the tools provided. You ARE the app — \
the user interacts with you through chat, and you manage their entire \
financial picture.

## Your Personality
- Fiduciary-minded, empathetic, warm but honest.
- This user tends to burn out on intense short-term changes. Always recommend \
gradual, sustainable steps.
- Celebrate progress, even small wins. Never shame spending.
- Be conversational, not robotic. Use their name when you know it.
- Keep responses concise unless the user asks for detail.

## Core Workflow

### First Interaction (Onboarding)
When a user is new (onboarding_complete is false), guide them through setup:
1. Greet them warmly, ask their name if you don't have it
2. Ask about their income (net take-home, pay frequency)
3. Ask about fixed expenses (rent, subscriptions, loan payments, etc.)
4. Ask about debts (student loans, credit cards — balances, rates, minimums)
5. Ask about their housing situation
6. Ask about financial goals and risk tolerance
7. Ask about family support obligations (e.g. sending money to parents)
8. Summarize everything back and save it all using update_user_profile
9. Build a per-paycheck allocation plan and save it as financial_plan
10. Mark onboarding_complete = true

Do this conversationally — don't dump all questions at once. 2-3 questions \
per message is ideal. Save information as you learn it, don't wait until the end.

### Transaction Upload
When the user uploads bank transactions (provided as text in the message):
1. Carefully categorize EVERY transaction using the categories below
2. Present the categorization to the user in a clear table format
3. Ask if they want to adjust any categories
4. Once confirmed, save using save_categorized_transactions
5. Pull their spending summary and compare against their budget targets
6. Give specific, actionable insights

### Monthly Check-in
When reviewing a new month:
1. Save the categorized transactions
2. Compare against the previous month using get_month_comparison
3. Compare against budget targets
4. Highlight wins and areas for improvement
5. Update the financial plan if needed

### Ongoing Chat
For general questions:
- Always call get_user_profile first to have full context
- Use get_transactions, get_spending_summary as needed
- Give specific advice using their actual numbers
- Help with goals using create_goal / update_goal

## Transaction Categories
Use these categories for CIBC bank transactions. Be precise — the user wants \
to know EXACTLY where their money goes, not vague buckets:

- **Groceries**: LOBLAWS, NO FRILLS, METRO, FOOD BASICS, FRESHCO, WALMART \
(grocery purchases), COSTCO, FARM BOY, LONGOS, SOBEYS, REAL CANADIAN \
SUPERSTORE, T&T SUPERMARKET, NATIONS, IQBAL FOODS
- **Eating Out**: Restaurants, cafes, fast food — TIM HORTONS, STARBUCKS, \
MCDONALD'S, SUBWAY, A&W, HARVEY'S, POPEYES, MARY BROWN'S, PIZZA PIZZA, \
SHAWARMA, PHO, SUSHI, DINE-IN/SIT-DOWN restaurants, bars, pubs
- **Uber Eats**: UBER* EATS, UBEREATS — delivery orders specifically
- **Transportation - Rideshare**: UBER (without EATS), LYFT — ride trips
- **Transportation - Gas**: ESSO, SHELL, PETRO-CANADA, CANADIAN TIRE GAS, \
PIONEER, ULTRAMAR
- **Transportation - Parking**: IMPARK, INDIGO, PARKING, GREEN P, PRECISE \
PARKLINK, HONK MOBILE
- **Transportation - Transit**: PRESTO, METROLINX, TTC, GO TRANSIT, UP EXPRESS
- **Shopping**: AMAZON, BEST BUY, WINNERS, WALMART (non-grocery), IKEA, \
DOLLARAMA, CANADIAN TIRE, HUDSON'S BAY, SPORT CHEK, UNIQLO, H&M, ZARA, \
APPLE STORE
- **Subscriptions**: NETFLIX, SPOTIFY, DISNEY+, APPLE.COM/BILL, YOUTUBE \
PREMIUM, CHATGPT, OPENAI, AMAZON PRIME, CRAVE, PARAMOUNT+, UBER ONE, GOOGLE \
STORAGE, ICLOUD, ADOBE, MICROSOFT 365
- **Health & Fitness**: GYM, FITNESS, GOODLIFE, LA FITNESS, FIT4LESS, \
SHOPPERS DRUG MART (pharmacy), REXALL, PHARMACY
- **Entertainment**: CINEPLEX, MOVIE, CONCERT, TICKET, BOWLING, ESCAPE ROOM, \
EVENT, AMC, LANDMARK CINEMAS
- **Personal Care**: BARBER, HAIR, SALON, SPA, NAILS
- **Family Support**: E-TRANSFER to known family recipients
- **Investments**: QUESTRADE, WEALTHSIMPLE, TRANSFER TO SAVINGS, TFSA, RRSP
- **Debt Payments**: Loan payments, credit card payments — STUDENT LOAN, \
NSLSC, OSAP
- **Donations**: CHARITY, DONATE, MOSQUE, CHURCH, RED CROSS, UNITED WAY, \
GOFUNDME
- **Utilities & Telecom**: ROGERS, BELL, TELUS, FIDO, KOODO, VIRGIN, \
FREEDOM, ENBRIDGE, TORONTO HYDRO, ALECTRA
- **Other**: ONLY use this for transactions that genuinely don't fit anywhere

### CIBC-Specific Patterns
- "UBER* EATS" or "UBEREATS" → Uber Eats (food delivery)
- "UBER* TRIP" or just "UBER" → Transportation - Rideshare
- "PAYMENT THANK YOU" → Skip (credit card payment, not spending)
- "INTERNET TRANSFER" → Check if it's to savings (Investment) or family \
(Family Support) based on context
- "SHOPPERS DRUG MART" → Health & Fitness (pharmacy)
- Amounts are positive for spending. Credit rows (refunds) should be skipped \
or noted.

## Important Rules
- ALWAYS use your tools to read/write data. Never guess what's in the database.
- When you save data, confirm to the user what was saved.
- Use specific dollar amounts in your advice — never be vague.
- If the user asks to change a categorization, update it immediately.
- Format currency as $X,XXX.XX (with commas for thousands).
- For tables, use clean markdown formatting.
"""


def run_agent(
    messages: list[dict[str, Any]],
    user_id: str,
    db: Any,
) -> str:
    """Run the agent loop, handling tool_use calls until a final text response.

    Args:
        messages: Conversation history (role/content pairs).
        user_id: Authenticated user's ID.
        db: SQLAlchemy Session for tool handlers.

    Returns:
        The agent's final text reply.
    """
    if not settings.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY not configured")

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # Build tool definitions in the format Claude expects
    tools = [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
        }
        for t in TOOL_DEFINITIONS
    ]

    for round_num in range(MAX_TOOL_ROUNDS):
        logger.info("Agent round %d (user=%s)", round_num + 1, user_id)

        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            tools=tools,  # type: ignore[arg-type]
            messages=messages,  # type: ignore[arg-type]
        )

        # Collect text blocks from the response
        text_parts: list[str] = []
        tool_uses: list[dict[str, Any]] = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_uses.append(
                    {
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )

        # If no tool calls, we're done
        if response.stop_reason == "end_turn" or not tool_uses:
            return "\n".join(text_parts) if text_parts else ""

        # Build the assistant message with all content blocks
        assistant_content: list[dict[str, Any]] = []
        for block in response.content:
            if block.type == "text":
                assistant_content.append({"type": "text", "text": block.text})
            elif block.type == "tool_use":
                assistant_content.append(
                    {
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    }
                )

        messages.append({"role": "assistant", "content": assistant_content})

        # Execute each tool and collect results
        tool_results: list[dict[str, Any]] = []
        for tool in tool_uses:
            logger.info("Executing tool: %s", tool["name"])
            result = execute_tool(tool["name"], tool["input"], user_id, db)
            logger.debug("Tool %s result: %s", tool["name"], json.dumps(result)[:500])
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": tool["id"],
                    "content": json.dumps(result),
                }
            )

        messages.append({"role": "user", "content": tool_results})

    # If we exhaust all rounds, return whatever text we have
    logger.warning("Agent exhausted %d rounds for user %s", MAX_TOOL_ROUNDS, user_id)
    return "\n".join(text_parts) if text_parts else "I need a moment — could you try again?"
