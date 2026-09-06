"""Resolves the Owner/Card rows a parsed transaction should attach to,
creating them on first sight. Kept separate from import_service so the
same lookup-or-create logic can be reused later (e.g. a manual
accounts/cards admin API)."""

from sqlalchemy.orm import Session

from app.models import Card, Owner

_DEFAULT_OWNER_NAME = "나"


def get_or_create_default_owner(db: Session) -> Owner:
    owner = db.query(Owner).filter_by(name=_DEFAULT_OWNER_NAME).first()
    if owner:
        return owner
    owner = Owner(name=_DEFAULT_OWNER_NAME)
    db.add(owner)
    db.flush()
    return owner


def get_or_create_card(
    db: Session, owner: Owner, institution: str, card_number_masked: str, card_type: str = "CREDIT"
) -> Card:
    card = (
        db.query(Card)
        .filter_by(institution=institution, card_number_masked=card_number_masked)
        .first()
    )
    if card:
        return card
    card = Card(
        owner_id=owner.id,
        institution=institution,
        card_number_masked=card_number_masked,
        card_type=card_type,
    )
    db.add(card)
    db.flush()
    return card
