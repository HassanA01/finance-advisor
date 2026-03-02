import uuid
from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base


class MonthlyReport(Base):
    __tablename__ = "monthly_reports"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    month_key = Column(String, nullable=False)

    spending = Column(JSON)
    vs_target = Column(JSON)
    vs_prev_month = Column(JSON)

    summary = Column(Text)
    insights = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="monthly_reports")

    __table_args__ = (
        UniqueConstraint("user_id", "month_key", name="unique_user_month"),
    )
