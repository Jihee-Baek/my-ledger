"""돈이 계좌(결제수단)로 들어왔는지(IN) 나갔는지(OUT).

수입/지출은 타입 자체가 방향이지만, 이체(TRANSFER)는 방향이 없는 타입이라 원본 행에서
읽어야 한다. 방향을 따로 저장해 두면 '수입 <-> 이체', '지출 <-> 이체' 전환을 안전하게
허용할 수 있다 (들어온 돈을 지출로 바꾸는 식의 잘못된 전환을 막는다).
"""

from decimal import Decimal, InvalidOperation

IN = "IN"
OUT = "OUT"

# 방향별로 서로 바꿀 수 있는 타입
ALLOWED_TYPES = {IN: {"INCOME", "TRANSFER"}, OUT: {"EXPENSE", "TRANSFER"}}


def _num(value) -> Decimal:
    try:
        return Decimal(str(value).replace(",", "").strip() or "0")
    except (InvalidOperation, AttributeError):
        return Decimal(0)


def infer_direction(source: str, transaction_type: str, raw_row: dict | None) -> str:
    if transaction_type == "INCOME":
        return IN
    if transaction_type == "EXPENSE":
        return OUT
    raw = raw_row or {}
    if source == "shinhan_bank":
        return IN if _num(raw.get("입금")) > 0 else OUT
    if source == "manual_bank_csv":
        return IN if _num(raw.get("amount")) > 0 else OUT
    if source == "gimpo_pay":
        # 충전: 은행에서 김포페이 잔액으로 들어온 돈
        return IN if raw.get("거래방식") == "충전" else OUT
    return OUT
