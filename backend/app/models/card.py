from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Card(Base):
    """A credit/debit card. Numbers are stored pre-masked
    (e.g. '1234-****-****-5678') - the full card number is never persisted."""

    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("owners.id"))
    settlement_account_id: Mapped[int | None] = mapped_column(ForeignKey("accounts.id"))
    institution: Mapped[str] = mapped_column(String(100), nullable=False)
    card_name: Mapped[str | None] = mapped_column(String(200))
    card_number_masked: Mapped[str | None] = mapped_column(String(50))
    card_type: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    owner: Mapped["Owner"] = relationship(back_populates="cards")
