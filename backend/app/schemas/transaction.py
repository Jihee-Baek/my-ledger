from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    transaction_date: date
    transaction_time: time | None
    transaction_type: str
    amount: Decimal
    currency: str
    merchant_raw: str | None
    description: str | None
    memo: str | None
    category_id: int | None
    category_confirmed: bool
    is_excluded: bool
    card_id: int | None
    account_id: int | None
    source: str
    created_at: datetime


class TransactionListOut(BaseModel):
    items: list[TransactionOut]
    total: int
    limit: int
    offset: int


class TransactionUpdate(BaseModel):
    category_id: int | None = None
    memo: str | None = None
