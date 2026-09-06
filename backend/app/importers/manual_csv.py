"""Hand-transcribed bank statement CSV (for institutions that only give
you an app screenshot or a paper statement - e.g. 기업은행 앱 캡처).

Format (UTF-8, comma separated):

    # my-ledger manual bank statement v1
    # institution: 기업은행
    # account: 입출금            (optional, shown as the masked account label)
    # owner: 홍길동              (optional; counterparties starting with it -> TRANSFER)
    date,time,counterparty,amount,balance,type,memo
    2026-05-04,07:16,대출이자 32-00031,-197260,52740,,메모

  * amount: signed - negative = 출금(EXPENSE), positive = 입금(INCOME)
  * balance: optional, but when present the importer re-computes the running
    balance in chronological order and refuses the file on any mismatch -
    this is what makes a manual transcription trustworthy.
  * type: optional override (EXPENSE / INCOME / TRANSFER); blank = by sign,
    except self-transfers detected via the owner header.
  * memo -> description; the first header line is the format sentinel.
"""

import csv
import re
from decimal import Decimal
from pathlib import Path

from app.importers.base import ParsedTransaction
from app.importers.normalize import parse_amount, parse_date, parse_time

_SENTINEL = "# my-ledger manual bank statement v1"
_REQUIRED = {"date", "time", "counterparty", "amount"}
_VALID_TYPES = {"EXPENSE", "INCOME", "TRANSFER"}


class ManualBankCsvImporter:
    source = "manual_bank_csv"

    def can_handle(self, file_path: Path) -> bool:
        try:
            with file_path.open("r", encoding="utf-8-sig") as f:
                return f.readline().strip() == _SENTINEL
        except (OSError, UnicodeDecodeError):
            return False

    def parse(self, file_path: Path) -> list[ParsedTransaction]:
        meta: dict[str, str] = {}
        data_lines: list[str] = []
        with file_path.open("r", encoding="utf-8-sig") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                if stripped.startswith("#"):
                    if m := re.match(r"#\s*([a-z_]+)\s*:\s*(.*)$", stripped):
                        meta[m.group(1)] = m.group(2).strip()
                    continue
                data_lines.append(line)

        institution = meta.get("institution")
        if not institution:
            raise ValueError("manual CSV: '# institution:' 헤더가 필요합니다")
        account_label = meta.get("account") or "계좌"
        owner = meta.get("owner", "")

        reader = csv.DictReader(data_lines)
        missing = _REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"manual CSV: 컬럼 누락 {sorted(missing)}")

        rows = []
        for lineno, row in enumerate(reader, start=2):
            amount = parse_amount(row["amount"])
            if amount == 0:
                continue
            balance_raw = (row.get("balance") or "").strip()
            rows.append(
                {
                    "lineno": lineno,
                    "date": parse_date(row["date"]),
                    "time": parse_time(row["time"]),
                    "counterparty": (row["counterparty"] or "").strip(),
                    "amount": amount,
                    "balance": parse_amount(balance_raw) if balance_raw else None,
                    "type": (row.get("type") or "").strip().upper(),
                    "memo": (row.get("memo") or "").strip(),
                }
            )

        self._verify_balance_chain(rows)

        results = []
        for r in rows:
            tx_type = r["type"]
            if tx_type and tx_type not in _VALID_TYPES:
                raise ValueError(f"manual CSV {r['lineno']}행: type 값이 잘못됨 {tx_type!r}")
            if not tx_type:
                if owner and r["counterparty"].startswith(owner):
                    tx_type = "TRANSFER"
                else:
                    tx_type = "EXPENSE" if r["amount"] < 0 else "INCOME"

            time_key = r["time"].strftime("%H%M%S") if r["time"] else "000000"
            results.append(
                ParsedTransaction(
                    transaction_date=r["date"],
                    transaction_time=r["time"],
                    transaction_type=tx_type,
                    amount=abs(r["amount"]),
                    currency="KRW",
                    merchant_raw=r["counterparty"] or "(내용 없음)",
                    card_institution=institution,
                    card_number_masked=account_label,
                    card_type="BANK",
                    source_transaction_id=f"{r['date'].isoformat()}T{time_key}-{r['amount']}",
                    description=r["memo"] or None,
                    raw_row={
                        "date": r["date"].isoformat(),
                        "time": r["time"].isoformat() if r["time"] else None,
                        "counterparty": r["counterparty"],
                        "amount": str(r["amount"]),
                        "balance": str(r["balance"]) if r["balance"] is not None else None,
                        "memo": r["memo"],
                    },
                )
            )
        return results

    @staticmethod
    def _verify_balance_chain(rows: list[dict]) -> None:
        """prev.balance + amount == balance for every consecutive pair that has
        balances. A single typo in a hand-typed file breaks the chain, so this
        is the safety net for transcription errors."""
        ordered = sorted(rows, key=lambda r: (r["date"], r["time"] or __import__("datetime").time.min, r["lineno"]))
        prev = None
        for r in ordered:
            if r["balance"] is None:
                prev = None
                continue
            if prev is not None:
                expected = prev["balance"] + r["amount"]
                if expected != r["balance"]:
                    raise ValueError(
                        f"manual CSV {r['lineno']}행 잔액 불일치: 직전 잔액 {prev['balance']:,} "
                        f"{r['amount']:+,} = {expected:,} 이어야 하는데 {r['balance']:,} 로 적혀 있음"
                    )
            prev = r
