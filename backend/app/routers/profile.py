from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User, UserProfile
from app.schemas.profile import ProfileResponse, ProfileUpdate
from app.utils.auth import get_current_user

router = APIRouter(prefix="/profile", tags=["profile"])


def _get_profile(user: User, db: Session) -> UserProfile:
    profile = db.query(UserProfile).filter(UserProfile.user_id == user.id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile


@router.get("", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _get_profile(current_user, db)


@router.put("", response_model=ProfileResponse)
def update_profile(
    body: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_profile(current_user, db)
    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.patch("/onboarding-complete", response_model=ProfileResponse)
def complete_onboarding(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = _get_profile(current_user, db)
    profile.onboarding_complete = True  # type: ignore[assignment]
    db.commit()
    db.refresh(profile)
    return profile
