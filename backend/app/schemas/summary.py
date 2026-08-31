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
