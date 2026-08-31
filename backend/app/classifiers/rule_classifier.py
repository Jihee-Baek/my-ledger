import re

from sqlalchemy.orm import Session

from app.classifiers.merchant import get_or_create_merchant
from app.models import CategoryRule, Merchant, Transaction


def _rule_matches(rule: CategoryRule, merchant_raw: str, description: str | None) -> bool:
    haystacks = [merchant_raw or "", description or ""]
    keyword = rule.keyword

    if rule.match_type == "EXACT":
        return any(h.strip() == keyword for h in haystacks)
    if rule.match_type == "REGEX":
        return any(re.search(keyword, h) for h in haystacks)
    return any(keyword in h for h in haystacks)  # CONTAINS (default)


def classify_transaction(db: Session, transaction: Transaction) -> bool:
    """Assigns transaction.category_id if it isn't already set by a user.
    Order: (1) a merchant's learned default_category_id, (2) enabled
    CategoryRules by priority. Returns True if a category was assigned."""

    if transaction.category_confirmed:
        return False  # never override a user-confirmed category

    merchant = get_or_create_merchant(db, transaction.merchant_raw)
    transaction.merchant_id = merchant.id

    if merchant.default_category_id is not None:
        transaction.category_id = merchant.default_category_id
        return True

    rules = (
        db.query(CategoryRule)
        .filter_by(enabled=True)
        .order_by(CategoryRule.priority.desc(), CategoryRule.id.asc())
        .all()
    )
    for rule in rules:
        if _rule_matches(rule, transaction.merchant_raw, transaction.description):
            transaction.category_id = rule.category_id
            if merchant.default_category_id is None:
                merchant.default_category_id = rule.category_id
            return True

    return False


def set_user_category(db: Session, transaction: Transaction, category_id: int) -> None:
    """A manual correction (design doc section 8: 사용자가 수정한 분류가
    향후 동일 가맹점의 분류에 반영). Updates both this transaction and the
    merchant's learned default, so future imports of the same merchant
    classify correctly without needing a new CategoryRule."""

    transaction.category_id = category_id
    transaction.category_confirmed = True

    if transaction.merchant_id is None:
        merchant = get_or_create_merchant(db, transaction.merchant_raw)
        transaction.merchant_id = merchant.id
    else:
        merchant = db.get(Merchant, transaction.merchant_id)

    merchant.default_category_id = category_id
