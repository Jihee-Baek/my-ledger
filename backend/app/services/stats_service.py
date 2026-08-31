"""All amount aggregation lives here so it happens exactly once, in one
place, in the backend - not duplicated in the MCP server and never
delegated to an LLM (design doc section 9/17).

Currency safety: KRW and foreign-currency (e.g. USD) transactions are
NEVER summed together. Every aggregation is scoped to a single
`currency` (default "KRW", since that's the overwhelming majority of
spend); foreign-currency totals are reported separately, never blended
into a KRW figure.
"""

import calendar
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Category, MonthlyBudget, Transaction


def set_budget(
    db: Session, year: int, month: int, amount: Decimal, category_id: int | None
) -> MonthlyBudget:
    """Upsert - re-setting the same (year, month, category) updates the
    amount rather than erroring on the unique constraint. monthly_budgets.amount
    is an Integer (whole KRW won, unlike transactions.amount) so the
    sqlite3 driver needs an int, not a Decimal."""
    amount_int = int(amount)
    budget = (
        db.query(MonthlyBudget)
        .filter_by(year=year, month=month, category_id=category_id)
        .first()
    )
    if budget:
        budget.amount = amount_int
    else:
        budget = MonthlyBudget(year=year, month=month, category_id=category_id, amount=amount_int)
        db.add(budget)
    db.commit()
    db.refresh(budget)
    return budget


def month_bounds(year: int, month: int) -> tuple[date, date]:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def _category_display_name(category: Category | None) -> str:
    return category.name if category else "미분류"


def _trailing_year_months(end_year: int, end_month: int, count: int) -> list[tuple[int, int]]:
    months = []
    y, m = end_year, end_month
    for _ in range(count):
        months.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(months))


def monthly_trend(
    db: Session,
    months: int = 6,
    end_year: int | None = None,
    end_month: int | None = None,
    currency: str = "KRW",
) -> list[dict]:
    """Total income/expense for each of the trailing `months` calendar
    months, ending at (end_year, end_month) - or at the most recent
    transaction's month if not given, for the same reason
    recurring_expenses anchors on data rather than wall-clock 'today'."""

    if end_year is None or end_month is None:
        latest = db.scalar(select(func.max(Transaction.transaction_date)))
        if latest is None:
            return []
        end_year, end_month = latest.year, latest.month

    results = []
    for year, month in _trailing_year_months(end_year, end_month, months):
        start, end = month_bounds(year, month)
        income = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
                Transaction.is_excluded.is_(False),
                Transaction.transaction_type == "INCOME",
                Transaction.currency == currency,
            )
        )
        expense = db.scalar(
            select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                Transaction.transaction_date >= start,
                Transaction.transaction_date <= end,
                Transaction.is_excluded.is_(False),
                Transaction.transaction_type == "EXPENSE",
                Transaction.currency == currency,
            )
        )
        income = Decimal(income or 0)
        expense = Decimal(expense or 0)
        results.append(
            {
                "year": year,
                "month": month,
                "total_income": income,
                "total_expense": expense,
                "net": income - expense,
            }
        )
    return results


def monthly_summary(db: Session, year: int, month: int, currency: str = "KRW") -> dict:
    start, end = month_bounds(year, month)

    base = select(Transaction).where(
        Transaction.transaction_date >= start,
        Transaction.transaction_date <= end,
        Transaction.is_excluded.is_(False),
    )

    def total_for(transaction_type: str, ccy: str) -> Decimal:
        stmt = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
            Transaction.is_excluded.is_(False),
            Transaction.transaction_type == transaction_type,
            Transaction.currency == ccy,
        )
        return Decimal(db.scalar(stmt) or 0)

    total_income = total_for("INCOME", currency)
    total_expense = total_for("EXPENSE", currency)

    # Category breakdown (EXPENSE only, this currency only)
    rows = db.execute(
        select(
            Transaction.category_id,
            func.sum(Transaction.amount).label("amount"),
        )
        .where(
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
            Transaction.is_excluded.is_(False),
            Transaction.transaction_type == "EXPENSE",
            Transaction.currency == currency,
        )
        .group_by(Transaction.category_id)
    ).all()

    category_ids = [r.category_id for r in rows if r.category_id is not None]
    categories = {c.id: c for c in db.query(Category).filter(Category.id.in_(category_ids)).all()}

    top_categories = []
    for category_id, amount in rows:
        name = _category_display_name(categories.get(category_id)) if category_id else "미분류"
        pct = float(amount) / float(total_expense) * 100 if total_expense else 0.0
        top_categories.append({"category": name, "amount": amount, "percentage": round(pct, 1)})
    top_categories.sort(key=lambda c: c["amount"], reverse=True)

    # Other currencies present in this month, so nothing silently disappears
    other_currency_rows = db.execute(
        select(Transaction.currency, func.sum(Transaction.amount))
        .where(
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
            Transaction.is_excluded.is_(False),
            Transaction.transaction_type == "EXPENSE",
            Transaction.currency != currency,
        )
        .group_by(Transaction.currency)
    ).all()

    return {
        "year": year,
        "month": month,
        "currency": currency,
        "total_income": total_income,
        "total_expense": total_expense,
        "net": total_income - total_expense,
        "top_categories": top_categories,
        "other_currencies": [
            {"currency": ccy, "total_expense": Decimal(amount)} for ccy, amount in other_currency_rows
        ],
    }


def category_summary(
    db: Session, start_date: date, end_date: date, currency: str = "KRW"
) -> list[dict]:
    rows = db.execute(
        select(Transaction.category_id, func.sum(Transaction.amount).label("amount"))
        .where(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.is_excluded.is_(False),
            Transaction.transaction_type == "EXPENSE",
            Transaction.currency == currency,
        )
        .group_by(Transaction.category_id)
    ).all()

    # Load every category, not just the ones directly used as a leaf
    # category_id: a parent (e.g. 식비) is often never itself assigned to
    # a transaction, but is still needed here to resolve its children's
    # parent_category name.
    categories = {c.id: c for c in db.query(Category).all()}
    total = sum((amount for _, amount in rows), Decimal(0))

    results = []
    for category_id, amount in rows:
        category = categories.get(category_id) if category_id else None
        parent = categories.get(category.parent_id) if category and category.parent_id else None
        pct = float(amount) / float(total) * 100 if total else 0.0
        results.append(
            {
                "category_id": category_id,
                "category": _category_display_name(category),
                "parent_category": parent.name if parent else None,
                "amount": amount,
                "percentage": round(pct, 1),
            }
        )
    results.sort(key=lambda r: r["amount"], reverse=True)
    return results


def merchant_summary(
    db: Session, start_date: date, end_date: date, currency: str = "KRW", limit: int = 10
) -> list[dict]:
    rows = db.execute(
        select(
            Transaction.merchant_raw,
            func.sum(Transaction.amount).label("amount"),
            func.count().label("cnt"),
        )
        .where(
            Transaction.transaction_date >= start_date,
            Transaction.transaction_date <= end_date,
            Transaction.is_excluded.is_(False),
            Transaction.transaction_type == "EXPENSE",
            Transaction.currency == currency,
        )
        .group_by(Transaction.merchant_raw)
        .order_by(func.sum(Transaction.amount).desc())
        .limit(limit)
    ).all()

    return [
        {"merchant": merchant or "(알수없음)", "amount": amount, "count": cnt}
        for merchant, amount, cnt in rows
    ]


def merchant_summary_range(
    db: Session, end_year: int, end_month: int, months: int = 1, currency: str = "KRW", limit: int = 10
) -> list[dict]:
    """Same as merchant_summary, but spanning the trailing `months`
    calendar months ending at (end_year, end_month) instead of a single
    month - e.g. "최근 6개월 동안 가장 많이 쓴 가맹점"."""
    window = _trailing_year_months(end_year, end_month, months)
    start = month_bounds(*window[0])[0]
    end = month_bounds(end_year, end_month)[1]
    return merchant_summary(db, start, end, currency, limit)


def compare_months(
    db: Session,
    base_year: int,
    base_month: int,
    target_year: int,
    target_month: int,
    currency: str = "KRW",
) -> list[dict]:
    base_summary = {
        c["category"]: c["amount"] for c in category_summary(db, *month_bounds(base_year, base_month), currency)
    }
    target_summary = {
        c["category"]: c["amount"]
        for c in category_summary(db, *month_bounds(target_year, target_month), currency)
    }

    all_categories = set(base_summary) | set(target_summary)
    results = []
    for name in all_categories:
        base_amount = base_summary.get(name, Decimal(0))
        target_amount = target_summary.get(name, Decimal(0))
        diff = target_amount - base_amount
        pct = float(diff) / float(base_amount) * 100 if base_amount else None
        results.append(
            {
                "category": name,
                "base_amount": base_amount,
                "target_amount": target_amount,
                "diff": diff,
                "diff_percentage": round(pct, 1) if pct is not None else None,
            }
        )
    results.sort(key=lambda r: r["diff"], reverse=True)
    return results


@dataclass
class _MerchantMonthAgg:
    total: Decimal = Decimal(0)
    count: int = 0


def recurring_expenses(
    db: Session, months: int = 3, min_months_seen: int = 2, currency: str = "KRW"
) -> list[dict]:
    """A merchant counts as 'recurring' if it has at least one EXPENSE
    transaction in `min_months_seen` distinct calendar months within the
    trailing `months`-month window. The window ends at the most recent
    transaction date in the DB (not wall-clock 'today'), since this is
    an offline tool working from whatever CSV history has been
    imported, not a live feed."""

    latest = db.scalar(select(func.max(Transaction.transaction_date)))
    if latest is None:
        return []

    window_start_year = latest.year
    window_start_month = latest.month - (months - 1)
    while window_start_month <= 0:
        window_start_month += 12
        window_start_year -= 1
    window_start, _ = month_bounds(window_start_year, window_start_month)

    rows = db.execute(
        select(
            Transaction.merchant_raw,
            Transaction.transaction_date,
            Transaction.amount,
        ).where(
            Transaction.transaction_date >= window_start,
            Transaction.transaction_date <= latest,
            Transaction.is_excluded.is_(False),
            Transaction.transaction_type == "EXPENSE",
            Transaction.currency == currency,
            Transaction.merchant_raw.is_not(None),
        )
    ).all()

    by_merchant: dict[str, dict[str, _MerchantMonthAgg]] = defaultdict(dict)
    for merchant_raw, tx_date, amount in rows:
        ym = f"{tx_date.year:04d}-{tx_date.month:02d}"
        agg = by_merchant[merchant_raw].setdefault(ym, _MerchantMonthAgg())
        agg.total += amount
        agg.count += 1

    results = []
    for merchant, months_map in by_merchant.items():
        if len(months_map) < min_months_seen:
            continue
        monthly_totals = [agg.total for agg in months_map.values()]
        occurrences = sum(agg.count for agg in months_map.values())
        results.append(
            {
                "merchant": merchant,
                "months_seen": len(months_map),
                "occurrences": occurrences,
                "average_amount": sum(monthly_totals, Decimal(0)) / len(monthly_totals),
                "last_amount": monthly_totals[-1],
            }
        )
    results.sort(key=lambda r: r["months_seen"], reverse=True)
    return results


def _category_and_descendant_ids(db: Session, category_id: int) -> list[int]:
    """A budget set on a parent category (e.g. 식비) must count spend
    recorded against its subcategories (외식/카페/...) too, since
    transactions are always classified onto a leaf category, never the
    parent itself."""
    ids = [category_id]
    children = db.query(Category.id).filter(Category.parent_id == category_id).all()
    ids.extend(c.id for c in children)
    return ids


def budget_status(db: Session, year: int, month: int, currency: str = "KRW") -> list[dict]:
    budgets = db.query(MonthlyBudget).filter_by(year=year, month=month).all()
    if not budgets:
        return []

    start, end = month_bounds(year, month)
    overall_actual = db.scalar(
        select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.transaction_date >= start,
            Transaction.transaction_date <= end,
            Transaction.is_excluded.is_(False),
            Transaction.transaction_type == "EXPENSE",
            Transaction.currency == currency,
        )
    )

    results = []
    for budget in budgets:
        if budget.category_id is None:
            actual = Decimal(overall_actual or 0)
            name = "전체"
        else:
            category_ids = _category_and_descendant_ids(db, budget.category_id)
            actual = Decimal(
                db.scalar(
                    select(func.coalesce(func.sum(Transaction.amount), 0)).where(
                        Transaction.transaction_date >= start,
                        Transaction.transaction_date <= end,
                        Transaction.is_excluded.is_(False),
                        Transaction.transaction_type == "EXPENSE",
                        Transaction.currency == currency,
                        Transaction.category_id.in_(category_ids),
                    )
                )
                or 0
            )
            category = db.get(Category, budget.category_id)
            name = _category_display_name(category)

        remaining = budget.amount - actual
        pct = float(actual) / float(budget.amount) * 100 if budget.amount else None
        results.append(
            {
                "category_id": budget.category_id,
                "category": name,
                "budgeted": budget.amount,
                "actual": actual,
                "remaining": remaining,
                "percentage_used": round(pct, 1) if pct is not None else None,
            }
        )
    return results


def spending_anomalies(
    db: Session,
    year: int,
    month: int,
    lookback_months: int = 3,
    min_change_pct: float = 30.0,
    currency: str = "KRW",
) -> dict:
    """Design doc section 9.4: compute the comparison Backend-side (this
    month vs. the trailing average) and hand the LLM only the already-
    correct numbers - it explains, it doesn't calculate.

    A category counts as anomalous if it moved by at least
    `min_change_pct` versus its trailing average, or if it has spend
    this month but none at all in the lookback window (a genuinely new
    expense, not just a percentage swing)."""

    baseline_months = _trailing_year_months(year, month, lookback_months + 1)[:-1]

    baseline_category_totals: dict[str, Decimal] = defaultdict(Decimal)
    baseline_overall_total = Decimal(0)
    for by, bm in baseline_months:
        start, end = month_bounds(by, bm)
        for row in category_summary(db, start, end, currency):
            baseline_category_totals[row["category"]] += row["amount"]
            baseline_overall_total += row["amount"]

    denom = len(baseline_months) or 1
    baseline_category_avg = {name: total / denom for name, total in baseline_category_totals.items()}
    baseline_overall_avg = baseline_overall_total / denom

    current_start, current_end = month_bounds(year, month)
    current_rows = category_summary(db, current_start, current_end, currency)
    current_by_category = {row["category"]: row["amount"] for row in current_rows}
    current_overall = sum((row["amount"] for row in current_rows), Decimal(0))

    def change_pct(current: Decimal, baseline: Decimal) -> float | None:
        if baseline == 0:
            return None  # brand new spend - flagged separately, not as a %
        return float((current - baseline) / baseline * 100)

    overall_pct = change_pct(current_overall, baseline_overall_avg)

    all_categories = set(current_by_category) | set(baseline_category_avg)
    flagged = []
    for name in all_categories:
        current_amount = current_by_category.get(name, Decimal(0))
        baseline_avg = baseline_category_avg.get(name, Decimal(0))
        pct = change_pct(current_amount, baseline_avg)
        is_new = baseline_avg == 0 and current_amount > 0
        if is_new or (pct is not None and abs(pct) >= min_change_pct):
            flagged.append(
                {
                    "category": name,
                    "current_amount": current_amount,
                    "baseline_average": baseline_avg,
                    "change_percentage": round(pct, 1) if pct is not None else None,
                    "is_new": is_new,
                }
            )
    flagged.sort(key=lambda r: abs(r["change_percentage"]) if r["change_percentage"] is not None else float(r["current_amount"]), reverse=True)

    return {
        "year": year,
        "month": month,
        "lookback_months": lookback_months,
        "currency": currency,
        "overall": {
            "current_total": current_overall,
            "baseline_average": baseline_overall_avg,
            "change_percentage": round(overall_pct, 1) if overall_pct is not None else None,
        },
        "categories": flagged,
    }
