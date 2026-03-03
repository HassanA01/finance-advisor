from datetime import datetime

from pydantic import BaseModel, ConfigDict


class GoalCreate(BaseModel):
    name: str
    target_amount: float
    deadline: datetime | None = None


class GoalUpdate(BaseModel):
    name: str | None = None
    target_amount: float | None = None
    current_amount: float | None = None
    deadline: datetime | None = None
    status: str | None = None


class GoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    target_amount: float
    current_amount: float
    deadline: datetime | None
    status: str
    created_at: datetime
    updated_at: datetime
