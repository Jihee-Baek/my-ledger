"""신한체크 '대중교통 이용내역' Excel export (real .xlsx, single flat sheet).

One row per tag-on/tag-off ride (지하철/버스), which is far too noisy to
keep as individual transactions - so this adapter aggregates all rides
of a calendar month into a single EXPENSE dated on the last day of that
month. The per-ride rows are preserved verbatim in raw_row["rides"] for
auditability.

There is no per-ride 승인번호 in this export, so the synthetic
source_transaction_id "transit-YYYY-MM" keeps re-imports of the same
month idempotent. Caveat: the fingerprint also includes the amount, so
re-importing a month whose export previously covered only part of the
month would add a second (larger) row - re-export whole months only.
"""

import calendar
from datetime import date
from decimal import Decimal
from pathlib import Path

import openpyxl

from app.importers.base import ParsedTransaction
from app.importers.normalize import parse_amount, parse_date
from app.importers.sniff import is_real_xlsx

_EXPECTED_HEADER = {
    "구분", "교통수단", "이용장소", "거래일", "승차역명", "하차역명",
    "카드번호", "총이용금액",
}


def _last_day(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


class ShinhanTransitImporter:
    source = "shinhan_check_transit"

    def can_handle(self, file_path: Path) -> bool:
        if not is_real_xlsx(file_path):
            return False
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True)
            header = next(wb.active.iter_rows(values_only=True))
        except Exception:
            return False
        return _EXPECTED_HEADER.issubset(set(header))

    def parse(self, file_path: Path) -> list[ParsedTransaction]:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb.active
        header, *data_rows = ws.iter_rows(values_only=True)

        # (year, month, masked_card) -> aggregate
        buckets: dict[tuple[int, int, str], dict] = {}
        for values in data_rows:
            row = dict(zip(header, values))
            if not row.get("거래일"):  # trailing summary/blank row
                continue
            ride_date = parse_date(str(row["거래일"]))
            amount = parse_amount(str(row["총이용금액"]).replace("원", ""))
            card = str(row.get("카드번호") or "").strip()

            key = (ride_date.year, ride_date.month, card)
            bucket = buckets.setdefault(
                key, {"amount": Decimal("0"), "rides": []}
            )
            bucket["amount"] += amount
            bucket["rides"].append(
                {k: v for k, v in row.items() if v not in (None, "", "-")}
            )

        results = []
        for (year, month, card), bucket in sorted(buckets.items()):
            ride_count = len(bucket["rides"])
            results.append(
                ParsedTransaction(
                    transaction_date=_last_day(year, month),
                    transaction_type="EXPENSE",
                    amount=bucket["amount"],
                    currency="KRW",
                    merchant_raw="대중교통(지하철/버스)",
                    card_institution="신한카드",
                    card_number_masked=card,
                    source_transaction_id=f"transit-{year:04d}-{month:02d}",
                    description=f"신한체크 대중교통 {year}년 {month}월분 {ride_count}건 합산",
                    raw_row={"rides": bucket["rides"]},
                )
            )
        return results
