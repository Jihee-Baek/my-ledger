from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Card
from app.schemas.card import CardOut, CardUpdate

router = APIRouter(tags=["cards"])


@router.get("/cards", response_model=list[CardOut])
def list_cards(db: Session = Depends(get_db)):
    return db.query(Card).order_by(Card.institution, Card.id).all()


@router.patch("/cards/{card_id}", response_model=CardOut)
def update_card(card_id: int, body: CardUpdate, db: Session = Depends(get_db)):
    """결제수단 별칭 변경. 빈 문자열이면 별칭을 지운다."""
    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(status_code=404, detail="Card not found")
    card.card_name = (body.card_name or "").strip() or None
    db.commit()
    db.refresh(card)
    return card
