"""Query building for transactions. Kept as plain SQLAlchemy Query
objects (not raw SQL strings) so a future swap to PostgreSQL only
requires changing the engine/session, not this layer."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models import Transaction


@dataclass
class TransactionFilters:
    start_date: date | None = None
    end_date: date | None = None
    min_amount: Decimal | None = None
    max_amount: Decimal | None = None
    category_id: int | None = None
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
        stmt = stmt.where(Transaction.category_id == filters.category_id)
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
