"""Shared parsing helpers used across adapters."""

import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

_DATE_PATTERNS = [
    "%Y.%m.%d %H:%M",
    "%Y.%m.%d %H:%M:%S",
    "%Y.%m.%d",
    "%Y년 %m월 %d일",
    "%Y-%m-%d",
]

_KOREAN_DATE_RE = re.compile(r"(\d{4})년\s*(\d{2})월\s*(\d{2})일")


def parse_date(raw: str) -> date:
    raw = raw.strip()
    match = _KOREAN_DATE_RE.match(raw)
    if match:
        y, m, d = match.groups()
        return date(int(y), int(m), int(d))

    for pattern in _DATE_PATTERNS:
        try:
            return datetime.strptime(raw, pattern).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognized date format: {raw!r}")


def parse_amount(raw) -> Decimal:
    if isinstance(raw, (int, float, Decimal)):
        return Decimal(str(raw))
    text = str(raw).strip().replace(",", "")
    if not text:
        raise ValueError("Empty amount")
    try:
        return Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"Unrecognized amount format: {raw!r}") from exc


_FULL_CARD_NUMBER_RE = re.compile(r"\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{2,4}")


def mask_card_number_if_needed(raw: str) -> str:
    """Defense in depth: source files are expected to arrive pre-masked,
    but if a fully unmasked 16-digit-ish number slips through, mask it
    before it ever reaches the database."""
    raw = raw.strip()
    if "*" in raw:
        return raw
    if _FULL_CARD_NUMBER_RE.fullmatch(raw.replace(" ", "")):
        digits = re.sub(r"[- ]", "", raw)
        return f"{digits[:4]}-****-****-{digits[-4:]}"
    return raw


_TRUTHY_CANCEL_VALUES = {"취소", "취소완료", "Y", "y"}
_FALSY_VALUES = {"", "-", None}


def is_cancelled(value) -> bool:
    if value in _FALSY_VALUES:
        return False
    return str(value).strip() not in _FALSY_VALUES and str(value).strip() != "0"


def mark_cancelled_pairs(transactions: list) -> None:
    """Some card exports record a cancellation as its own row (a
    negative-amount reversal with the same 승인번호/source_transaction_id
    as the original charge) rather than flagging the original row
    itself. If only the reversal row is excluded from stats, the
    original charge still counts as spend even though it net out to
    zero - so once any row in a source_transaction_id group is
    excluded, every row sharing that id must be excluded too."""

    by_source_id: dict[str, list] = {}
    for parsed in transactions:
        if parsed.source_transaction_id:
            by_source_id.setdefault(parsed.source_transaction_id, []).append(parsed)

    for group in by_source_id.values():
        if len(group) > 1 and any(p.is_excluded for p in group):
            for p in group:
                p.is_excluded = True
