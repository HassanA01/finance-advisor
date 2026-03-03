from typing import Any

from pydantic import BaseModel, ConfigDict


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    net_monthly_income: float | None
    pay_frequency: str | None
    fixed_expenses: dict[str, Any]
    debts: list[Any]
    budget_targets: dict[str, Any]
    family_support_recipients: list[str]
    emergency_fund: float
    risk_tolerance: str
    onboarding_complete: bool


class ProfileUpdate(BaseModel):
    net_monthly_income: float | None = None
    pay_frequency: str | None = None
    fixed_expenses: dict[str, Any] | None = None
    debts: list[Any] | None = None
    budget_targets: dict[str, Any] | None = None
    family_support_recipients: list[str] | None = None
    emergency_fund: float | None = None
    risk_tolerance: str | None = None
