from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CurrencyTotal(BaseModel):
    currency: str
    total_expense: Decimal


class CategoryAmount(BaseModel):
    category: str
    amount: Decimal
    percentage: float


class MonthlySummaryOut(BaseModel):
    year: int
    month: int
    currency: str
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    top_categories: list[CategoryAmount]
    other_currencies: list[CurrencyTotal]


class CategorySummaryItem(BaseModel):
    category_id: int | None
    category: str
    parent_category: str | None
    amount: Decimal
    percentage: float


class MerchantSummaryItem(BaseModel):
    merchant: str
    amount: Decimal
    count: int


class MonthComparisonItem(BaseModel):
    category: str
    base_amount: Decimal
    target_amount: Decimal
    diff: Decimal
    diff_percentage: float | None


class RecurringExpenseItem(BaseModel):
    merchant: str
    months_seen: int
    occurrences: int
    average_amount: Decimal
    last_amount: Decimal


class BudgetStatusItem(BaseModel):
    category_id: int | None
    category: str
    budgeted: Decimal
    actual: Decimal
    remaining: Decimal
    percentage_used: float | None


class AnomalyOverall(BaseModel):
    current_total: Decimal
    baseline_average: Decimal
    change_percentage: float | None


class AnomalyCategory(BaseModel):
    category: str
    current_amount: Decimal
    baseline_average: Decimal
    change_percentage: float | None
    is_new: bool


class SpendingAnomalies(BaseModel):
    year: int
    month: int
    lookback_months: int
    currency: str
    overall: AnomalyOverall
    categories: list[AnomalyCategory]


class MonthlyTrendItem(BaseModel):
    year: int
    month: int
    total_income: Decimal
    total_expense: Decimal
    net: Decimal


class BudgetSet(BaseModel):
    year: int
    month: int
    amount: Decimal
    category_id: int | None = None  # None = 전체(월 총) 예산


class BreakdownItem(BaseModel):
    category_id: int | None
    category: str
    amount: Decimal
    count: int
    percentage: float


class BreakdownOut(BaseModel):
    """통계 화면용: 기간 내 수입/지출 총액과, 선택한 유형의 카테고리별 비중.
    parent_id 없음 -> 상위 카테고리별(하위는 상위로 합산), 있음 -> 그 하위별."""

    start_date: date
    end_date: date
    currency: str
    transaction_type: str
    total_income: Decimal
    total_expense: Decimal
    parent_id: int | None
    parent_name: str | None
    total: Decimal
    count: int
    items: list[BreakdownItem]
