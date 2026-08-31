"""현대카드 '실시간 이용내역' export - an HTML table saved with a .xls
extension (not real Excel). The table carries trailing '소계'/'합계'
summary rows that must be dropped."""

from pathlib import Path

import pandas as pd

from app.importers.base import ParsedTransaction
from app.importers.normalize import (
    is_cancelled,
    mask_card_number_if_needed,
    parse_amount,
    parse_date,
)
from app.importers.sniff import is_html

_MARKER = "실시간 이용내역"


class HyundaiCardImporter:
    source = "hyundai_card"

    def can_handle(self, file_path: Path) -> bool:
        if not is_html(file_path):
            return False
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        return _MARKER in text

    def parse(self, file_path: Path) -> list[ParsedTransaction]:
        tables = pd.read_html(file_path, header=2)
        df = tables[0]

        results = []
        for _, row in df.iterrows():
            row = row.to_dict()
            if not row.get("승인일") or str(row["승인일"]).strip() == "-":
                continue  # trailing 소계/합계 row

            source_transaction_id = row.get("승인번호")
            results.append(
                ParsedTransaction(
                    transaction_date=parse_date(str(row["승인일"])),
                    transaction_type="EXPENSE",
                    amount=parse_amount(row["승인금액"]),
                    currency="KRW",
                    merchant_raw=str(row["가맹점명"]).strip(),
                    card_institution="현대카드",
                    card_number_masked=mask_card_number_if_needed(str(row["카드종류"])),
                    source_transaction_id=(
                        str(int(source_transaction_id)) if pd.notna(source_transaction_id) else None
                    ),
                    is_excluded=is_cancelled(row.get("취소일")),
                    raw_row=row,
                )
            )
        return results
