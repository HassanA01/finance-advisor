import io
from datetime import datetime

import pandas as pd

from app.utils.categories import categorize_transaction


def parse_csv(
    content: bytes,
    filename: str,
    family_recipients: list[str] | None = None,
) -> list[dict[str, object]]:
    """Parse a CIBC CSV file and return a list of transaction dicts."""
    df = pd.read_csv(io.BytesIO(content))
    df.columns = df.columns.str.strip()

    transactions: list[dict[str, object]] = []

    # Detect format: debit (Date, Transaction, Debit, Credit) vs credit (Date, Transaction, Payment, Credit)
    cols = [c.lower() for c in df.columns]
    is_credit_card = "payment" in cols

    for _, row in df.iterrows():
        description = str(row.get("Transaction", "")).strip()
        if not description:
            continue

        # Parse date
        date_str = str(row.get("Date", "")).strip()
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            try:
                date = datetime.strptime(date_str, "%m/%d/%Y")
            except ValueError:
                continue

        # Get amount
        if is_credit_card:
            # Credit card: Payment column = payments, Credit column = charges
            payment = _parse_float(row.get("Payment"))
            credit = _parse_float(row.get("Credit"))
            if payment and payment > 0:
                # Skip payment rows
                continue
            amount = credit if credit else 0.0
        else:
            # Debit: Debit column = money out, Credit column = money in
            debit = _parse_float(row.get("Debit"))
            credit = _parse_float(row.get("Credit"))
            if debit and debit > 0:
                amount = debit
            elif credit and credit > 0:
                # Money in — skip or categorize as income
                continue
            else:
                continue

        if amount <= 0:
            continue

        category = categorize_transaction(description, family_recipients)

        # Skip credit card payment rows
        if category == "Credit Card Payment":
            continue

        source = "credit_card" if is_credit_card else "debit"
        month_key = date.strftime("%Y-%m")

        transactions.append(
            {
                "date": date,
                "description": description,
                "amount": round(amount, 2),
                "category": category,
                "source": source,
                "month_key": month_key,
            }
        )

    return transactions


def _parse_float(value: object) -> float | None:
    if pd.isna(value):  # type: ignore[arg-type]
        return None
    try:
        s = str(value).replace("$", "").replace(",", "").strip()
        return float(s) if s else None
    except (ValueError, TypeError):
        return None
