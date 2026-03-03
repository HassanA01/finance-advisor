from typing import Any

from pydantic import BaseModel, ConfigDict


class CategorySpending(BaseModel):
    category: str
    amount: float
    target: float | None = None
    vs_target: float | None = None  # amount - target (positive = over budget)
    prev_amount: float | None = None
    vs_prev: float | None = None  # amount - prev_amount


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    month_key: str
    spending: dict[str, Any]
    vs_target: dict[str, Any]
    vs_prev_month: dict[str, Any]
    total_spent: float
    total_target: float | None
    categories: list[CategorySpending]
    summary: str | None = None
    insights: list[Any] | None = None
