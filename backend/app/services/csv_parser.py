import io
import logging
from datetime import datetime

import pandas as pd

from app.utils.categories import categorize_transaction

logger = logging.getLogger(__name__)


def parse_csv(
    content: bytes,
    filename: str,
    family_recipients: list[str] | None = None,
) -> list[dict[str, object]]:
    """Parse a CIBC CSV file and return a list of transaction dicts.

    Supports both header and headerless formats:
    - Debit (4 cols): date, transaction, debit, credit
    - Credit card (5 cols): date, transaction, debit, credit, card#
    """
    has_headers = _has_headers(content)

    if has_headers:
        logger.info("Parsing %s (detected: has headers)", filename)
        df = pd.read_csv(io.BytesIO(content))
        df.columns = df.columns.str.strip()
        return _parse_with_headers(df, filename, family_recipients)
    else:
        logger.info("Parsing %s (detected: headerless)", filename)
        df = pd.read_csv(io.BytesIO(content), header=None)
        return _parse_headerless(df, filename, family_recipients)


def _has_headers(content: bytes) -> bool:
    """Detect whether the CSV has a header row.

    Reads the first line and tries to parse the first cell as a date.
    If it parses as a date, the CSV is headerless (first row is data).
    """
    first_line = content.split(b"\n", 1)[0].decode("utf-8", errors="replace").strip()
    if not first_line:
        return True  # Empty file, default to header mode

    first_cell = first_line.split(",")[0].strip().strip('"')
    return _try_parse_date(first_cell) is None


def _try_parse_date(value: str) -> datetime | None:
    """Try parsing a string as a date. Returns datetime or None."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _parse_with_headers(
    df: pd.DataFrame,
    filename: str,
    family_recipients: list[str] | None,
) -> list[dict[str, object]]:
    """Parse a CSV that has column headers (Date, Transaction, Debit/Payment, Credit)."""
    transactions: list[dict[str, object]] = []

    cols = [c.lower() for c in df.columns]
    is_credit_card = "payment" in cols
    logger.info(
        "%s: format=%s, rows=%d",
        filename,
        "credit_card" if is_credit_card else "debit",
        len(df),
    )

    for idx, row in df.iterrows():
        description = str(row.get("Transaction", "")).strip()
        if not description:
            continue

        date_str = str(row.get("Date", "")).strip()
        date = _try_parse_date(date_str)
        if date is None:
            logger.warning("%s row %s: could not parse date '%s'", filename, idx, date_str)
            continue

        if is_credit_card:
            payment = _parse_float(row.get("Payment"))
            credit = _parse_float(row.get("Credit"))
            if payment and payment > 0:
                logger.debug("%s row %s: skipping payment row", filename, idx)
                continue
            amount = credit if credit else 0.0
        else:
            debit = _parse_float(row.get("Debit"))
            credit = _parse_float(row.get("Credit"))
            if debit and debit > 0:
                amount = debit
            elif credit and credit > 0:
                logger.debug("%s row %s: skipping credit (money in)", filename, idx)
                continue
            else:
                continue

        if amount <= 0:
            continue

        category = categorize_transaction(description, family_recipients)
        if category == "Credit Card Payment":
            logger.debug("%s row %s: skipping credit card payment", filename, idx)
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

    logger.info("%s: parsed %d transactions", filename, len(transactions))
    return transactions


def _parse_headerless(
    df: pd.DataFrame,
    filename: str,
    family_recipients: list[str] | None,
) -> list[dict[str, object]]:
    """Parse a headerless CIBC CSV by column index.

    4 columns: date, description, debit, credit (debit card)
    5 columns: date, description, debit, credit, card# (credit card)
    """
    transactions: list[dict[str, object]] = []
    num_cols = len(df.columns)
    is_credit_card = num_cols >= 5
    source = "credit_card" if is_credit_card else "debit"

    logger.info(
        "%s: headerless format=%s, cols=%d, rows=%d",
        filename,
        source,
        num_cols,
        len(df),
    )

    for idx, row in df.iterrows():
        date_str = str(row.iloc[0]).strip()
        date = _try_parse_date(date_str)
        if date is None:
            logger.warning("%s row %s: could not parse date '%s'", filename, idx, date_str)
            continue

        description = str(row.iloc[1]).strip()
        if not description:
            continue

        debit = _parse_float(row.iloc[2])
        credit = _parse_float(row.iloc[3]) if num_cols > 3 else None

        # Debit column = money out (expenses) — use these
        # Credit column = money in (paycheques, etc.) — skip
        if debit and debit > 0:
            amount = debit
        elif credit and credit > 0:
            logger.debug("%s row %s: skipping credit (money in)", filename, idx)
            continue
        else:
            continue

        if amount <= 0:
            continue

        category = categorize_transaction(description, family_recipients)
        if category == "Credit Card Payment":
            logger.debug("%s row %s: skipping credit card payment", filename, idx)
            continue

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

    logger.info("%s: parsed %d transactions", filename, len(transactions))
    return transactions


def _parse_float(value: object) -> float | None:
    if pd.isna(value):  # type: ignore[arg-type]
        return None
    try:
        s = str(value).replace("$", "").replace(",", "").strip()
        return float(s) if s else None
    except (ValueError, TypeError):
        return None
