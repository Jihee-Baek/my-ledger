from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class RawTransaction(Base):
    """The original CSV row, preserved verbatim as JSON text. Kept
    separate from `transactions` so normalization/classification logic
    can be re-run from the source data without re-importing files."""

    __tablename__ = "raw_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    import_batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id"), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_data: Mapped[str] = mapped_column(Text, nullable=False)
    row_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    import_batch: Mapped["ImportBatch"] = relationship(back_populates="raw_transactions")
