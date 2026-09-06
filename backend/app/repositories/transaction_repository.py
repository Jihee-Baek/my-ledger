"""Query building for transactions. Kept as plain SQLAlchemy Query
objects (not raw SQL strings) so a future swap to PostgreSQL only
requires changing the engine/session, not this layer."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.models import Category, Transaction


@dataclass
class TransactionFilters:
    start_date: date | None = None
    end_date: date | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    category_id: int | None = None
    uncategorized: bool = False  # True -> only rows without a category
    card_id: int | None = None
    merchant: str | None = None  # substring match against merchant_raw
    q: str | None = None  # substring match against merchant_raw or description
    transaction_type: str | None = None
    currency: str | None = None
    include_excluded: bool = False
    sort_by: str = "date"  # "date" | "amount"
    sort_dir: str = "desc"  # "asc" | "desc"


def _apply_filters(stmt: Select, filters: TransactionFilters) -> Select:
    if filters.start_date is not None:
        stmt = stmt.where(Transaction.transaction_date >= filters.start_date)
    if filters.end_date is not None:
        stmt = stmt.where(Transaction.transaction_date <= filters.end_date)
    if filters.min_amount is not None:
        stmt = stmt.where(Transaction.amount >= filters.min_amount)
    if filters.max_amount is not None:
        stmt = stmt.where(Transaction.amount <= filters.max_amount)
    if filters.category_id is not None:
        # 상위 카테고리(예: 식비)를 고르면 그 하위(외식/배달/카페...)에 분류된 거래까지
        # 모두 포함한다. 카테고리 트리는 2단계이므로 자식 한 단계만 펼치면 충분하다.
        subtree = select(Category.id).where(
            or_(Category.id == filters.category_id, Category.parent_id == filters.category_id)
        )
        stmt = stmt.where(Transaction.category_id.in_(subtree))
    if filters.uncategorized:
        # 이체(TRANSFER)는 카테고리가 필요 없는 자금 이동이므로 '미분류' 목록에서 제외
        stmt = stmt.where(
            Transaction.category_id.is_(None), Transaction.transaction_type != "TRANSFER"
        )
    if filters.card_id is not None:
        stmt = stmt.where(Transaction.card_id == filters.card_id)
    if filters.merchant:
        stmt = stmt.where(Transaction.merchant_raw.contains(filters.merchant))
    if filters.q:
        like = f"%{filters.q}%"
        stmt = stmt.where(
            (Transaction.merchant_raw.like(like)) | (Transaction.description.like(like))
        )
    if filters.transaction_type is not None:
        stmt = stmt.where(Transaction.transaction_type == filters.transaction_type)
    if filters.currency is not None:
        stmt = stmt.where(Transaction.currency == filters.currency)
    if not filters.include_excluded:
        stmt = stmt.where(Transaction.is_excluded.is_(False))
    return stmt


def search(
    db: Session, filters: TransactionFilters, limit: int, offset: int
) -> tuple[list[Transaction], int]:
    base = _apply_filters(select(Transaction), filters)

    total = db.scalar(select_count(base))

    sort_column = Transaction.amount if filters.sort_by == "amount" else Transaction.transaction_date
    order = sort_column.asc() if filters.sort_dir == "asc" else sort_column.desc()
    stmt = base.order_by(order, Transaction.id.desc())
    stmt = stmt.limit(limit).offset(offset)
    items = list(db.scalars(stmt).all())
    return items, total


def select_count(stmt: Select):
    from sqlalchemy import func

    return select(func.count()).select_from(stmt.order_by(None).subquery())


def get_by_id(db: Session, transaction_id: int) -> Transaction | None:
    return db.get(Transaction, transaction_id)


def totals_by_type(db: Session, filters: TransactionFilters) -> dict[str, tuple[int, Decimal]]:
    """{transaction_type: (count, sum)} over the filtered set."""
    from sqlalchemy import func

    base = _apply_filters(select(Transaction), filters).subquery()
    rows = db.execute(
        select(base.c.transaction_type, func.count(), func.sum(base.c.amount)).group_by(
            base.c.transaction_type
        )
    ).all()
    return {t: (int(n), Decimal(str(s or 0))) for t, n, s in rows}


def expense_by_category(db: Session, filters: TransactionFilters) -> list[tuple[int | None, Decimal]]:
    """[(category_id, sum)] of EXPENSE rows in the filtered set."""
    from sqlalchemy import func

    base = _apply_filters(select(Transaction), filters).subquery()
    rows = db.execute(
        select(base.c.category_id, func.sum(base.c.amount))
        .where(base.c.transaction_type == "EXPENSE")
        .group_by(base.c.category_id)
    ).all()
    return [(cid, Decimal(str(s or 0))) for cid, s in rows]


def expense_by_merchant(
    db: Session, filters: TransactionFilters, limit: int
) -> list[tuple[str | None, Decimal]]:
    from sqlalchemy import func

    base = _apply_filters(select(Transaction), filters).subquery()
    total = func.sum(base.c.amount)
    rows = db.execute(
        select(base.c.merchant_raw, total)
        .where(base.c.transaction_type == "EXPENSE")
        .group_by(base.c.merchant_raw)
        .order_by(total.desc())
        .limit(limit)
    ).all()
    return [(m, Decimal(str(s or 0))) for m, s in rows]


def period_expense_total(db: Session, filters: TransactionFilters) -> Decimal:
    """Denominator for '전체 지출 대비 비중': every non-excluded EXPENSE in the
    same date range and currency, ignoring category/card/type/text filters."""
    from sqlalchemy import func

    base_filters = TransactionFilters(
        start_date=filters.start_date, end_date=filters.end_date, currency=filters.currency
    )
    stmt = _apply_filters(select(func.sum(Transaction.amount)), base_filters).where(
        Transaction.transaction_type == "EXPENSE"
    )
    return Decimal(str(db.scalar(stmt) or 0))
