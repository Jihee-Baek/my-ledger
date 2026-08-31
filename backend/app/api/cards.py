from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models import Card
from app.schemas.card import CardOut

router = APIRouter(tags=["cards"])


@router.get("/cards", response_model=list[CardOut])
def list_cards(db: Session = Depends(get_db)):
    return db.query(Card).order_by(Card.institution, Card.id).all()
