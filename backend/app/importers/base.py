"""Common interface every card/bank adapter implements.

An adapter never touches the database - it only turns a downloaded
file into a list of ParsedTransaction. Everything DB-related (dedup,
account/card resolution, persistence) lives in
app.services.import_service, so adapters stay easy to unit test and
easy to add for a new institution.
"""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Protocol


@dataclass
class ParsedTransaction:
    transaction_date: date
    transaction_type: str  # INCOME / EXPENSE / TRANSFER
    amount: Decimal
    currency: str
    merchant_raw: str
    card_institution: str
    card_number_masked: str
    source_transaction_id: str | None = None
    description: str | None = None
    is_excluded: bool = False
    raw_row: dict = field(default_factory=dict)


class TransactionImporter(Protocol):
    source: str  # stable identifier, e.g. "samsung_card"

    def can_handle(self, file_path: Path) -> bool: ...

    def parse(self, file_path: Path) -> list[ParsedTransaction]: ...
