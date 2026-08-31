from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.summary import (
    BudgetSet,
    BudgetStatusItem,
    CategorySummaryItem,
    MerchantSummaryItem,
    MonthComparisonItem,
    MonthlySummaryOut,
    MonthlyTrendItem,
    RecurringExpenseItem,
    SpendingAnomalies,
)
from app.services import stats_service

router = APIRouter(tags=["stats"])


@router.get("/summary/monthly", response_model=MonthlySummaryOut)
def summary_monthly(year: int, month: int, currency: str = "KRW", db: Session = Depends(get_db)):
    return stats_service.monthly_summary(db, year, month, currency)


@router.get("/summary/category", response_model=list[CategorySummaryItem])
def summary_category(year: int, month: int, currency: str = "KRW", db: Session = Depends(get_db)):
    start, end = stats_service.month_bounds(year, month)
    return stats_service.category_summary(db, start, end, currency)


@router.get("/summary/merchant", response_model=list[MerchantSummaryItem])
def summary_merchant(
    year: int, month: int, currency: str = "KRW", limit: int = 10, db: Session = Depends(get_db)
):
    start, end = stats_service.month_bounds(year, month)
    return stats_service.merchant_summary(db, start, end, currency, limit)


@router.get("/summary/trend", response_model=list[MonthlyTrendItem])
def summary_trend(
    months: int = 6,
    end_year: int | None = None,
    end_month: int | None = None,
    currency: str = "KRW",
    db: Session = Depends(get_db),
):
    return stats_service.monthly_trend(db, months, end_year, end_month, currency)


@router.get("/comparison/month", response_model=list[MonthComparisonItem])
def comparison_month(
    base_year: int,
    base_month: int,
    target_year: int,
    target_month: int,
    currency: str = "KRW",
    db: Session = Depends(get_db),
):
    return stats_service.compare_months(
        db, base_year, base_month, target_year, target_month, currency
    )


@router.get("/recurring-expenses", response_model=list[RecurringExpenseItem])
def recurring_expenses(
    months: int = 3, min_months_seen: int = 2, currency: str = "KRW", db: Session = Depends(get_db)
):
    return stats_service.recurring_expenses(db, months, min_months_seen, currency)


@router.get("/anomalies", response_model=SpendingAnomalies)
def spending_anomalies(
    year: int,
    month: int,
    lookback_months: int = 3,
    min_change_pct: float = 30.0,
    currency: str = "KRW",
    db: Session = Depends(get_db),
):
    return stats_service.spending_anomalies(db, year, month, lookback_months, min_change_pct, currency)


@router.get("/budget", response_model=list[BudgetStatusItem])
def get_budget(year: int, month: int, currency: str = "KRW", db: Session = Depends(get_db)):
    return stats_service.budget_status(db, year, month, currency)


@router.post("/budget", response_model=BudgetStatusItem)
def set_budget(body: BudgetSet, db: Session = Depends(get_db)):
    stats_service.set_budget(db, body.year, body.month, body.amount, body.category_id)
    results = stats_service.budget_status(db, body.year, body.month)
    match = next((r for r in results if r["category_id"] == body.category_id), None)
    return match
