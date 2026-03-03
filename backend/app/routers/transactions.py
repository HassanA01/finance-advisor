from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User, UserProfile
from app.schemas.transaction import TransactionResponse, UploadResponse
from app.services.csv_parser import parse_csv
from app.utils.auth import get_current_user

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_transactions(
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    family_recipients: list[str] = list(profile.family_support_recipients) if profile else []

    uploaded = 0
    duplicates_skipped = 0
    months_affected: set[str] = set()

    for file in files:
        content = await file.read()
        parsed = parse_csv(content, file.filename or "unknown.csv", family_recipients)

        for txn in parsed:
            # Deduplicate: check for existing transaction with same date+description+amount
            existing = (
                db.query(Transaction)
                .filter(
                    Transaction.user_id == current_user.id,
                    Transaction.date == txn["date"],
                    Transaction.description == txn["description"],
                    Transaction.amount == txn["amount"],
                )
                .first()
            )
            if existing:
                duplicates_skipped += 1
                continue

            transaction = Transaction(
                user_id=str(current_user.id),
                date=txn["date"],
                description=str(txn["description"]),
                amount=float(str(txn["amount"])),
                category=str(txn["category"]),
                source=str(txn["source"]),
                month_key=str(txn["month_key"]),
            )
            db.add(transaction)
            uploaded += 1
            months_affected.add(str(txn["month_key"]))

    db.commit()

    return UploadResponse(
        uploaded=uploaded,
        duplicates_skipped=duplicates_skipped,
        months_affected=sorted(months_affected),
    )


@router.get("", response_model=list[TransactionResponse])
def list_transactions(
    month: str | None = Query(None, description="Filter by month (YYYY-MM)"),
    category: str | None = Query(None, description="Filter by category"),
    search: str | None = Query(None, description="Search in description"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)

    if month:
        query = query.filter(Transaction.month_key == month)
    if category:
        query = query.filter(Transaction.category == category)
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))

    return query.order_by(Transaction.date.desc()).all()


@router.get("/months", response_model=list[str])
def list_months(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = (
        db.query(Transaction.month_key)
        .filter(Transaction.user_id == current_user.id)
        .distinct()
        .order_by(Transaction.month_key.desc())
        .all()
    )
    return [r[0] for r in results]


@router.get("/categories", response_model=list[str])
def list_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    results = (
        db.query(Transaction.category)
        .filter(Transaction.user_id == current_user.id)
        .distinct()
        .order_by(Transaction.category)
        .all()
    )
    return [r[0] for r in results]
