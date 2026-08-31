"""Bulk-classify transactions and (for testing/demo) apply a manual
category correction the way a future PATCH /transactions/{id} endpoint
would.

Usage:
    ./.venv/bin/python -m app.classifiers.reclassify run
    ./.venv/bin/python -m app.classifiers.reclassify correct <transaction_id> <category_id>
"""

import sys

from app.classifiers.rule_classifier import classify_transaction, set_user_category
from app.core.db import SessionLocal
from app.models import Transaction


def classify_unclassified(db) -> tuple[int, int]:
    """Returns (classified_count, still_unclassified_count)."""
    transactions = (
        db.query(Transaction)
        .filter(Transaction.category_id.is_(None), Transaction.category_confirmed.is_(False))
        .all()
    )
    classified = 0
    for tx in transactions:
        if classify_transaction(db, tx):
            classified += 1
    db.commit()

    remaining = (
        db.query(Transaction)
        .filter(Transaction.category_id.is_(None))
        .count()
    )
    return classified, remaining


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)

    db = SessionLocal()
    try:
        if sys.argv[1] == "run":
            classified, remaining = classify_unclassified(db)
            print(f"{classified}건 자동 분류, {remaining}건 미분류로 남음.")
        elif sys.argv[1] == "correct":
            if len(sys.argv) != 4:
                raise SystemExit("Usage: reclassify correct <transaction_id> <category_id>")
            tx = db.get(Transaction, int(sys.argv[2]))
            if tx is None:
                raise SystemExit(f"Transaction {sys.argv[2]} not found")
            set_user_category(db, tx, int(sys.argv[3]))
            db.commit()
            print(f"Transaction {tx.id} -> category {tx.category_id} (user-confirmed)")
        else:
            raise SystemExit(__doc__)
    finally:
        db.close()


if __name__ == "__main__":
    main()
