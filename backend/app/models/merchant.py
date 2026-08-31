from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Merchant(Base):
    """A normalized merchant name (e.g. raw '스타벅스 강남2호점' -> '스타벅스').
    default_category_id is learned over time as the user confirms/corrects
    transaction categories for this merchant."""

    __tablename__ = "merchants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    default_category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    default_category: Mapped["Category | None"] = relationship()
