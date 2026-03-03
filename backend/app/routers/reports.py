from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.report import MonthlyReport
from app.models.transaction import Transaction
from app.models.user import User, UserProfile
from app.schemas.report import CategorySpending, ReportResponse
from app.services.advisor import analyze_month
from app.utils.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


def _prev_month_key(month_key: str) -> str:
    """Given 'YYYY-MM', return the previous month key."""
    dt = datetime.strptime(month_key, "%Y-%m")
    if dt.month == 1:
        return f"{dt.year - 1}-12"
    return f"{dt.year}-{dt.month - 1:02d}"


def _aggregate_spending(db: Session, user_id: str, month_key: str) -> dict[str, float]:
    """Sum transaction amounts by category for a given month."""
    rows = (
        db.query(Transaction.category, func.sum(Transaction.amount))
        .filter(Transaction.user_id == user_id, Transaction.month_key == month_key)
        .group_by(Transaction.category)
        .all()
    )
    return {cat: float(total) for cat, total in rows}


def _build_report(
    db: Session,
    user_id: str,
    month_key: str,
    profile: UserProfile | None,
) -> MonthlyReport:
    """Build a fresh report by aggregating transactions."""
    spending = _aggregate_spending(db, user_id, month_key)

    # Budget targets from profile
    targets: dict[str, float] = {}
    if profile and profile.budget_targets:
        targets = {k: float(v) for k, v in profile.budget_targets.items()}

    # vs_target: for each category with a target, compute difference
    vs_target: dict[str, dict[str, float]] = {}
    for cat, target in targets.items():
        actual = spending.get(cat, 0.0)
        vs_target[cat] = {
            "target": target,
            "actual": actual,
            "diff": round(actual - target, 2),
        }

    # Previous month spending
    prev_key = _prev_month_key(month_key)
    prev_spending = _aggregate_spending(db, user_id, prev_key)

    # vs_prev_month: for every category in current or previous
    all_cats = set(spending.keys()) | set(prev_spending.keys())
    vs_prev_month: dict[str, dict[str, float]] = {}
    for cat in all_cats:
        cur = spending.get(cat, 0.0)
        prev = prev_spending.get(cat, 0.0)
        vs_prev_month[cat] = {
            "current": cur,
            "previous": prev,
            "diff": round(cur - prev, 2),
        }

    # Generate AI analysis if there's spending data
    summary = None
    insights: list[str] = []
    if spending:
        profile_context = None
        if profile and profile.net_monthly_income:
            profile_context = {"net_monthly_income": float(profile.net_monthly_income)}
        summary, insights = analyze_month(spending, vs_target, vs_prev_month, profile_context)

    report = MonthlyReport(
        user_id=user_id,
        month_key=month_key,
        spending=spending,
        vs_target=vs_target,
        vs_prev_month=vs_prev_month,
        summary=summary or None,
        insights=insights or [],
    )
    return report


@router.get("/{month_key}", response_model=ReportResponse)
def get_report(
    month_key: str,
    regenerate: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    """Get or generate a monthly spending report."""
    # Validate month_key format
    try:
        datetime.strptime(month_key, "%Y-%m")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="month_key must be YYYY-MM format",
        )

    user_id = str(current_user.id)

    # Check for cached report
    if not regenerate:
        existing = (
            db.query(MonthlyReport)
            .filter(MonthlyReport.user_id == user_id, MonthlyReport.month_key == month_key)
            .first()
        )
        if existing:
            return _to_response(existing)

    # Get profile for targets
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    # Build fresh report
    report = _build_report(db, user_id, month_key, profile)

    # Upsert: delete old, insert new
    db.query(MonthlyReport).filter(
        MonthlyReport.user_id == user_id, MonthlyReport.month_key == month_key
    ).delete()
    db.add(report)
    db.commit()
    db.refresh(report)

    return _to_response(report)


def _to_response(report: MonthlyReport) -> ReportResponse:
    """Convert a MonthlyReport model to a ReportResponse with computed fields."""
    spending: dict[str, float] = dict(report.spending) if report.spending else {}
    vs_target: dict[str, dict[str, float]] = dict(report.vs_target) if report.vs_target else {}
    vs_prev: dict[str, dict[str, float]] = (
        dict(report.vs_prev_month) if report.vs_prev_month else {}
    )

    all_cats = set(spending.keys()) | set(vs_target.keys()) | set(vs_prev.keys())

    categories: list[CategorySpending] = []
    for cat in sorted(all_cats):
        amount = spending.get(cat, 0.0)
        target_info = vs_target.get(cat)
        prev_info = vs_prev.get(cat)

        categories.append(
            CategorySpending(
                category=cat,
                amount=round(amount, 2),
                target=target_info["target"] if target_info else None,
                vs_target=target_info["diff"] if target_info else None,
                prev_amount=prev_info["previous"] if prev_info else None,
                vs_prev=prev_info["diff"] if prev_info else None,
            )
        )

    total_spent = round(sum(spending.values()), 2)
    total_target = round(sum(t["target"] for t in vs_target.values()), 2) if vs_target else None

    return ReportResponse(
        id=str(report.id),
        month_key=str(report.month_key),
        spending=spending,
        vs_target=vs_target,
        vs_prev_month=vs_prev,
        total_spent=total_spent,
        total_target=total_target,
        categories=categories,
        summary=report.summary if isinstance(report.summary, str) else None,
        insights=report.insights if isinstance(report.insights, list) else None,
    )
