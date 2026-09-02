from datetime import date, time, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Transaction(Base):
    """A normalized, categorized transaction - the table statistics and
    MCP tools read from. `fingerprint` enforces de-duplication at the
    database level (see docs on the dedup strategy)."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    raw_transaction_id: Mapped[int | None] = mapped_column(ForeignKey("raw_transactions.id"))

    transaction_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    # 승인시각. 원본 export에 시각이 없는 경우(월 합산 대중교통 등)는 NULL.
    transaction_time: Mapped[time | None] = mapped_column(Time)
    transaction_type: Mapped[str] = mapped_column(String(10), nullable=False)  # INCOME/EXPENSE/TRANSFER
    # Numeric, not int: overseas transactions are recorded in their original
    # currency (e.g. USD) with cents, not whole KRW won.
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), default="KRW")

    merchant_raw: Mapped[str | None] = mapped_column(String(255))
    merchant_id: Mapped[int | None] = mapped_column(ForeignKey("merchants.id"))
    description: Mapped[str | None] = mapped_column(Text)
    memo: Mapped[str | None] = mapped_column(Text)

    account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), index=True)
    category_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_excluded: Mapped[bool] = mapped_column(Boolean, default=False)

    source: Mapped[str] = mapped_column(String(50), nullable=False)
    source_transaction_id: Mapped[str | None] = mapped_column(String(100))
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    merchant: Mapped["Merchant | None"] = relationship()
    category: Mapped["Category | None"] = relationship()
    account: Mapped["Account | None"] = relationship()
    card: Mapped["Card | None"] = relationship()
