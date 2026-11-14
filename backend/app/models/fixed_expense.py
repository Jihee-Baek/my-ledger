from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class FixedExpense(Base):
    """매달 나가는 고정 지출 항목. 거래를 직접 들고 있지 않고, 매칭 조건으로 지출 거래를 찾아 묶는다:
    가맹점명(공백 정리 후)에 keyword가 포함되고, card_id/amount가 지정돼 있으면 그것까지 일치해야 한다.
    amount는 같은 이름으로 두 건 이상 나가는 경우(예: DB손해보험 두 계약)를 가르기 위한 선택 조건."""

    __tablename__ = "fixed_expenses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    keyword: Mapped[str] = mapped_column(String(100), nullable=False)
    card_id: Mapped[int | None] = mapped_column(ForeignKey("cards.id"))
    amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    memo: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    card: Mapped["Card | None"] = relationship()
    category: Mapped["Category | None"] = relationship()
