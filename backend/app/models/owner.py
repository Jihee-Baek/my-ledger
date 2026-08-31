from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Owner(Base):
    """A household member. Kept separate from a login/auth concept -
    this only exists so accounts/cards/budgets can be attributed to a
    person, enabling a future shared household ledger."""

    __tablename__ = "owners"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    accounts: Mapped[list["Account"]] = relationship(back_populates="owner")
    cards: Mapped[list["Card"]] = relationship(back_populates="owner")
