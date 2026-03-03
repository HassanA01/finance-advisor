from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    date: datetime
    description: str
    amount: float
    category: str
    source: str
    month_key: str


class UploadResponse(BaseModel):
    uploaded: int
    duplicates_skipped: int
    months_affected: list[str]
