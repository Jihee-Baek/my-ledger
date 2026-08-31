"""Shapes a Transaction ORM row into the safe, minimal dict returned to
Claude - no full card/account numbers ever leave the DB (they're never
even stored), and only fields useful for answering ledger questions
are included."""

from sqlalchemy.orm import Session

from app.models import Card, Category, Transaction


def transaction_to_dict(db: Session, tx: Transaction) -> dict:
    category = db.get(Category, tx.category_id) if tx.category_id else None
    card = db.get(Card, tx.card_id) if tx.card_id else None

    return {
        "id": tx.id,
        "date": tx.transaction_date,
        "type": tx.transaction_type,
        "amount": tx.amount,
        "currency": tx.currency,
        "merchant": tx.merchant_raw,
        "description": tx.description,
        "memo": tx.memo,
        "category": category.name if category else None,
        "card": f"{card.institution} {card.card_number_masked}" if card else None,
        "is_excluded": tx.is_excluded,
    }
