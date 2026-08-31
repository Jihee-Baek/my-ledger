from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class MonthlyBudget(Base):
    """A budget for a given (owner, category, year, month).
    owner_id=None means a household-wide budget; category_id=None
    means the overall monthly budget rather than a per-category one."""

    __tablename__ = "monthly_budgets"
    __table_args__ = (
        UniqueConstraint("owner_id", "category_id", "year", "month", name="uq_budget_scope_period"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("owners.id"))
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)

    owner: Mapped["Owner | None"] = relationship()
    category: Mapped["Category | None"] = relationship()
