"""신한은행 '거래내역조회' PDF export (SOL 앱/인터넷뱅킹에서 저장한 명세).

One row per account movement with 출금/입금 columns, a 적요 (transaction
kind such as FB카드/자동이체/모바일) and 내용 (counterparty). There is no
per-row reference number, so a synthetic source_transaction_id built from
date+time+amounts keeps re-imports idempotent.

A bank statement overlaps heavily with the card exports already imported:
card bill settlements (FB카드/FB자동/카드결제) and 체크카드 debits are the
*same money* already recorded as individual card transactions. Counting
them again would double every card purchase, so:

  * card settlements  -> TRANSFER  (money moving to the card company)
  * 체크카드 debits    -> EXPENSE but is_excluded=True (kept for audit)
  * own-name transfers, 예금 해지, 1원 계좌 인증 -> TRANSFER

Everything else is EXPENSE (출금) or INCOME (입금) and goes through the
normal rule classifier. The account holder's name is read from the PDF
header only to detect self-transfers and is never persisted.
"""

import re
from decimal import Decimal
from pathlib import Path

from app.importers.base import ParsedTransaction
from app.importers.normalize import parse_amount, parse_date, parse_time
from app.importers.sniff import is_pdf

_EXPECTED_HEADER = ["거래일자", "거래시간", "적요", "출금(원)", "입금(원)", "내용", "잔액(원)", "거래점"]
_DATE_RE = re.compile(r"^\d{8}$")
_ACCOUNT_LIKE_RE = re.compile(r"^(\d{3}-\d{3,}|\d{10,})$")  # e.g. 304-1003 / 230368233284 (계좌번호)
_LEADING_CODE_RE = re.compile(r"^\d+\.")  # 자동이체 내용의 '020.' 같은 순번 접두어
_ACCOUNT_NO_RE = re.compile(r"\[신한\]\s*(\d{6,})")
_NAME_RE = re.compile(r"성명\s*(\S+)")

_CARD_SETTLEMENT_KINDS = {"FB카드", "FB자동", "카드결제"}
_CHECK_CARD_KINDS = {"체크카드"}
_TRANSFER_KINDS = {"해지"}  # 예적금 해지 입금 - 자기 자산 이동
# 카드사가 상대방인 입출금은 방향과 무관하게 카드 명세서와 같은 돈이다: 출금은 카드대금,
# 입금은 카드 취소/환불 정산으로 카드 내역에 이미 (취소 건으로) 반영되어 있다.
# 선불/지역화폐 충전: 통장에서 나간 돈은 잔액으로 옮겨진 것이고 실제 소비는 해당 서비스의
# 사용 내역을 따로 import해서 잡는다 (카드대금과 같은 구조).
_PREPAID_CHARGE_COUNTERPARTIES = {"김포페이"}
_CARD_COMPANIES = {"삼성카드", "신한카드", "현대카드", "현대카드(주)", "신한체크교통", "롯데카드", "KB국민카드", "우리카드", "하나카드", "BC카드"}


def _clean(cell) -> str:
    """Table cells wrap across lines inside the PDF ('타행인터넷\\n뱅킹')."""
    return re.sub(r"\s+", "", str(cell or ""))


def _mask_account(account_no: str) -> str:
    return f"{account_no[:3]}-***-***{account_no[-4:]}"


class ShinhanBankImporter:
    source = "shinhan_bank"

    def can_handle(self, file_path: Path) -> bool:
        if not is_pdf(file_path):
            return False
        try:
            import pdfplumber

            with pdfplumber.open(file_path) as pdf:
                text = pdf.pages[0].extract_text() or ""
        except Exception:
            return False
        return "거래내역조회" in text and "[신한]" in text and "SHINHANBANK" in text.replace(" ", "")

    def parse(self, file_path: Path) -> list[ParsedTransaction]:
        import pdfplumber

        owner_name = ""
        account_masked = "신한은행계좌"
        rows: list[list[str]] = []

        with pdfplumber.open(file_path) as pdf:
            first_text = pdf.pages[0].extract_text() or ""
            if m := _ACCOUNT_NO_RE.search(first_text):
                account_masked = _mask_account(m.group(1))
            if m := _NAME_RE.search(first_text):
                owner_name = m.group(1).strip()

            for page in pdf.pages:
                for table in page.extract_tables():
                    for raw in table:
                        cells = [str(c or "") for c in raw]
                        if len(cells) != len(_EXPECTED_HEADER):
                            continue
                        if not _DATE_RE.match(_clean(cells[0])):
                            continue  # header / summary block
                        rows.append(cells)

        results = []
        for cells in rows:
            row = dict(zip(_EXPECTED_HEADER, cells))
            kind = _clean(row["적요"])
            counterparty = re.sub(r"\s+", " ", row["내용"].replace("\n", "")).strip()
            withdrawal = parse_amount(row["출금(원)"] or "0")
            deposit = parse_amount(row["입금(원)"] or "0")
            if withdrawal == 0 and deposit == 0:
                continue

            tx_date = parse_date(f"{cells[0][:4]}-{cells[0][4:6]}-{cells[0][6:8]}")
            tx_time = parse_time(row["거래시간"])
            amount = withdrawal if withdrawal > 0 else deposit

            tx_type, is_excluded, description, merchant = self._interpret(
                kind, counterparty, withdrawal, deposit, owner_name
            )

            time_key = tx_time.strftime("%H%M%S") if tx_time else "000000"
            results.append(
                ParsedTransaction(
                    transaction_date=tx_date,
                    transaction_time=tx_time,
                    transaction_type=tx_type,
                    amount=amount,
                    currency="KRW",
                    merchant_raw=merchant,
                    card_institution="신한은행",
                    card_number_masked=account_masked,
                    card_type="BANK",
                    source_transaction_id=f"{cells[0]}{time_key}-{withdrawal}-{deposit}",
                    description=description,
                    is_excluded=is_excluded,
                    raw_row={
                        "거래일자": cells[0],
                        "거래시간": row["거래시간"],
                        "적요": kind,
                        "출금": str(withdrawal),
                        "입금": str(deposit),
                        "내용": counterparty,
                        "거래점": _clean(row["거래점"]),
                    },
                )
            )
        return results

    @staticmethod
    def _interpret(
        kind: str, counterparty: str, withdrawal: Decimal, deposit: Decimal, owner_name: str
    ) -> tuple[str, bool, str, str]:
        """-> (transaction_type, is_excluded, description, merchant_raw)"""
        merchant = counterparty or kind

        if kind in _CARD_SETTLEMENT_KINDS:
            return "TRANSFER", False, f"{kind} - 카드대금 결제 (카드 내역에 개별 거래로 이미 반영)", merchant
        if withdrawal > 0 and any(name in counterparty for name in _PREPAID_CHARGE_COUNTERPARTIES):
            return "TRANSFER", False, f"{kind} - {counterparty} 충전 (사용 내역을 별도 import하여 반영)", merchant
        if counterparty in _CARD_COMPANIES:
            what = "카드대금 결제" if withdrawal > 0 else "카드 취소/환불 정산"
            return "TRANSFER", False, f"{kind} - {what} (카드 내역에 이미 반영)", merchant
        if kind in _CHECK_CARD_KINDS:
            return "EXPENSE", True, f"{kind} - 신한카드 내역과 중복되어 통계에서 제외", merchant
        if kind in _TRANSFER_KINDS:
            return "TRANSFER", False, f"{kind} - 예적금 해지 입금", merchant
        if kind == "이자":
            return "INCOME", False, f"이자 {counterparty}".strip(), "예금이자"

        bare = _LEADING_CODE_RE.sub("", counterparty).strip()
        if "계좌개설" in bare or (withdrawal + deposit) == 1:
            return "TRANSFER", False, f"{kind} - 계좌 인증용 소액 이체", merchant
        if owner_name and bare.startswith(owner_name):
            return "TRANSFER", False, f"{kind} - 본인 계좌 간 이체", merchant
        if _ACCOUNT_LIKE_RE.match(bare):
            return "TRANSFER", False, f"{kind} - 계좌 이체 (계좌번호 앵커)", merchant

        if withdrawal > 0:
            return "EXPENSE", False, kind, merchant
        return "INCOME", False, kind, merchant
