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


class BreakdownItem(BaseModel):
    category: str  # label: 카테고리명 또는 가맹점명 (breakdown_kind에 따라)
    amount: Decimal
    percentage: float  # 필터된 지출 합계 대비 비중


class TransactionSummaryOut(BaseModel):
    currency: str
    count: int
    expense_count: int
    income_count: int
    transfer_count: int
    total_expense: Decimal
    total_income: Decimal
    total_transfer: Decimal
    period_expense_total: Decimal  # 같은 기간·통화의 전체 지출 (비중 계산의 분모)
    expense_share_pct: float | None  # total_expense / period_expense_total
    breakdown_kind: str  # parent | child | merchant
    breakdown: list[BreakdownItem]
