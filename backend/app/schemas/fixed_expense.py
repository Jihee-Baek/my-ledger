from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class FixedExpenseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    keyword: str = Field(min_length=1, max_length=100)
    card_id: int | None = None
    amount: Decimal | None = None
    category_id: int | None = None
    memo: str | None = None


class FixedExpenseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    keyword: str | None = Field(default=None, min_length=1, max_length=100)
    card_id: int | None = None
    amount: Decimal | None = None
    category_id: int | None = None
    memo: str | None = None
    is_active: bool | None = None


class FixedExpenseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    keyword: str
    card_id: int | None
    amount: Decimal | None
    category_id: int | None
    memo: str | None
    is_active: bool


class MonthAmount(BaseModel):
    month: str  # YYYY-MM
    amount: Decimal
    count: int = 0


class FixedExpenseRow(BaseModel):
    id: int
    name: str
    keyword: str
    amount_filter: Decimal | None
    card_id: int | None
    card_label: str | None
    category: str | None
    category_group: str
    memo: str | None
    pay_day: int | None  # 최근 6개월 결제일의 중앙값
    latest_amount: Decimal
    average_amount: Decimal
    months_paid: int
    last_paid_date: date | None
    selected_month_amount: Decimal
    status: str  # paid / upcoming / unconfirmed / missing
    monthly: list[MonthAmount]


class GroupTotal(BaseModel):
    group: str
    amount: Decimal
    percentage: float


class FixedExpenseCandidate(BaseModel):
    name: str
    keyword: str
    card_id: int | None
    card_label: str | None
    amount_filter: Decimal | None
    category_id: int | None
    category: str | None
    pay_day: int
    months_seen: int
    typical_amount: Decimal
    last_amount: Decimal


class FixedExpenseOverview(BaseModel):
    year: int
    month: int
    months: list[str]
    items: list[FixedExpenseRow]
    monthly_totals: list[MonthAmount]
    expected_monthly_total: Decimal
    selected_paid_total: Decimal
    selected_remaining_total: Decimal
    paid_count: int
    item_count: int
    group_totals: list[GroupTotal]
    candidates: list[FixedExpenseCandidate]
