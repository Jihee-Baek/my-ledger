from sqlalchemy.orm import Session

from app.classifiers.rule_classifier import set_user_category
from app.models import Transaction
from app.repositories.transaction_repository import (
    TransactionFilters,
    get_by_id,
    search,
)


def list_transactions(
    db: Session, filters: TransactionFilters, limit: int, offset: int
) -> tuple[list[Transaction], int]:
    return search(db, filters, limit, offset)


def get_transaction(db: Session, transaction_id: int) -> Transaction | None:
    return get_by_id(db, transaction_id)


def update_transaction(
    db: Session, transaction_id: int, category_id: int | None, memo: str | None
) -> Transaction | None:
    transaction = get_by_id(db, transaction_id)
    if transaction is None:
        return None

    if category_id is not None:
        set_user_category(db, transaction, category_id)
    if memo is not None:
        transaction.memo = memo

    db.commit()
    db.refresh(transaction)
    return transaction
