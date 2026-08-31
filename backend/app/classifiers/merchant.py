import re

from sqlalchemy.orm import Session

from app.models import Merchant


def normalize_merchant_name(raw: str) -> str:
    """Intentionally minimal for MVP: just trims/collapses whitespace.
    Branch-name variants of the same chain (e.g. '스타벅스 강남2호점' vs
    '스타벅스 서울역점') are left as distinct Merchant rows - keyword-based
    CategoryRules still classify both correctly, so there's no need for
    fuzzy merchant-name merging yet."""
    return re.sub(r"\s+", " ", raw.strip())


def get_or_create_merchant(db: Session, merchant_raw: str) -> Merchant:
    name = normalize_merchant_name(merchant_raw)
    merchant = db.query(Merchant).filter_by(name=name).first()
    if merchant:
        return merchant
    merchant = Merchant(name=name)
    db.add(merchant)
    db.flush()
    return merchant
