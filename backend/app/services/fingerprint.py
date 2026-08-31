import hashlib
import re

from app.importers.base import ParsedTransaction


def _normalize_merchant(name: str) -> str:
    return re.sub(r"\s+", "", name).lower()


def build_fingerprint(parsed: ParsedTransaction, source: str) -> str:
    """A stable, order-independent key for detecting the same transaction
    re-imported from the same or a different export of the same file.
    Prefers source_transaction_id when present (all three current
    adapters provide one); date+amount+merchant is the fallback for
    future institutions that don't."""

    parts = [
        source,
        parsed.card_number_masked,
        parsed.transaction_date.isoformat(),
        str(parsed.amount),
        _normalize_merchant(parsed.merchant_raw),
        parsed.source_transaction_id or "",
    ]
    digest_input = "|".join(parts).encode("utf-8")
    return hashlib.sha256(digest_input).hexdigest()
